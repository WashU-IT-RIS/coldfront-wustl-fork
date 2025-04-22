import os

from datetime import datetime
from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttribute,
    AllocationAttributeUsage,
)

from coldfront.plugins.qumulo.utils.acl_allocations import AclAllocations
from coldfront.plugins.qumulo.utils.qumulo_api import QumuloAPI


class FileQuotaService:

    @staticmethod
    def ingest_quotas_with_daily_usage(logger) -> None:
        filtering_by = lambda quota_usage: AclAllocations.is_base_allocation(
            quota_usage["path"]
        )
        base_allocation_quota_usages = FileQuotaService.get_allocation_file_quotas(
            filtering_by
        )
        _set_daily_quota_usages(base_allocation_quota_usages, logger)
        _validate_results(base_allocation_quota_usages, logger)

    @staticmethod
    def get_file_system_allocations_near_limit() -> list:
        filtering_by = lambda quota_usage: AclAllocations.is_base_allocation(
            quota_usage["path"]
        ) and _is_near_limit(quota_usage["capacity_usage"], quota_usage["limit"])
        allocations_over_threshold = FileQuotaService.get_allocation_file_quotas(
            filtering_by
        )

        return allocations_over_threshold

    @staticmethod
    def get_allocation_file_quotas(filtering_by: callable) -> list:
        qumulo_api = QumuloAPI()
        quota_usages = qumulo_api.get_all_quotas_with_usage()["quotas"]
        file_system_allocations = list(
            filter(
                filtering_by,
                quota_usages,
            )
        )
        return file_system_allocations

    @staticmethod
    def get_limit_threshold() -> float:
        limit_threshold = os.environ.get("ALLOCATION_LIMIT_THRESHOLD") or 0.9
        return float(limit_threshold)


def _set_daily_quota_usages(quotas, logger) -> None:
    for quota in quotas:

        allocation = _get_allocation(quota, logger)
        if allocation is None:
            continue
        allocation.set_usage("storage_quota", quota.get("capacity_usage"))


def _get_allocation(quota, logger) -> Allocation:
    path = quota.get("path")

    allocation = _get_allocation_by_attribute(path, logger)
    if allocation is None:
        if path[-1] != "/":
            return None

        value = path[:-1]
        logger.warn(f"Attempting to find allocation without the trailing slash...")
        allocation = _get_allocation_by_attribute(value, logger)

    return allocation


def _get_allocation_by_attribute(value, logger) -> Allocation:
    try:
        attribute = AllocationAttribute.objects.select_related("allocation").get(
            value=value,
            allocation_attribute_type__name="storage_filesystem_path",
            allocation__status__name="Active",
        )
    except AllocationAttribute.DoesNotExist:
        logger.warn(f"Allocation record for {value} path was not found")
        return None

    logger.warn(f"Allocation record for {value} path was found")
    return attribute.allocation


def _validate_results(quota_usages, logger) -> bool:
    today = datetime.today()
    year = today.year
    month = today.month
    day = today.day

    daily_usage_ingested = AllocationAttributeUsage.objects.filter(
        modified__year=year, modified__month=month, modified__day=day
    ).count()
    usage_pulled_from_qumulo = len(quota_usages)

    success = usage_pulled_from_qumulo == daily_usage_ingested
    if success:
        logger.warn("Successful ingestion of quota daily usage.")
    else:
        logger.warn(
            "Unsuccessful ingestion of quota daily usage. Not all the QUMULO usage data was stored in Coldfront."
        )
        logger.warn(f"Usages pulled from QUMULO: {usage_pulled_from_qumulo}")
        logger.warn(f"Usages ingested for today: {daily_usage_ingested}")

    return success


def _is_near_limit(usage: str, limit: str) -> bool:
    usage = int(usage)
    limit = int(limit)
    return (usage / limit) >= FileQuotaService.get_limit_threshold()
