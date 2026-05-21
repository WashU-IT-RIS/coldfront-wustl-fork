import json
import os

from datetime import datetime
from typing import Optional
from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttribute,
    AllocationAttributeUsage,
)

from coldfront.plugins.qumulo.utils.acl_allocations import AclAllocations
from coldfront.plugins.qumulo.utils.qumulo_api import QumuloAPI
from coldfront.plugins.qumulo.utils.storage_controller import StorageControllerFactory


def ingest_quotas_with_daily_usage(logger) -> None:
    connection_info = json.loads(os.environ.get("QUMULO_INFO"))
    base_allocation_quota_usages = []
    for storage_key in connection_info.keys():
        qumulo_api_conn = StorageControllerFactory().create_connection(storage_key)

        filtering_by = lambda quota_usage: AclAllocations.is_base_allocation(
            quota_usage["path"], storage_key
        )

        base_allocation_quota_usages += _get_allocation_file_quotas(
            qumulo_api_conn=qumulo_api_conn, filtering_by=filtering_by
        )
    _set_daily_quota_usages(base_allocation_quota_usages, logger)
    _validate_results(base_allocation_quota_usages, logger)


def get_file_system_allocations_near_limit() -> list:
    connection_info = json.loads(os.environ.get("QUMULO_INFO"))
    allocations_over_threshold = []
    for storage_key in connection_info.keys():
        qumulo_api_conn = StorageControllerFactory().create_connection(storage_key)

        filtering_by = lambda quota_usage: AclAllocations.is_base_allocation(
            quota_usage["path"], storage_key
        ) and _is_near_limit(
            int(quota_usage["capacity_usage"]), int(quota_usage["limit"])
        )

        allocations_over_threshold += _get_allocation_file_quotas(
            qumulo_api_conn=qumulo_api_conn, filtering_by=filtering_by
        )

    return allocations_over_threshold


def get_storage_limit_threshold() -> float:
    storage_limit_threshold = os.environ.get("ALLOCATION_NEAR_LIMIT_THRESHOLD") or 0.9
    return float(storage_limit_threshold)


def _get_allocation_file_quotas(
    qumulo_api_conn: QumuloAPI, filtering_by: callable
) -> list:
    quota_usages = qumulo_api_conn.get_all_quotas_with_usage()["quotas"]
    file_system_allocations = list(
        filter(
            filtering_by,
            quota_usages,
        )
    )
    return file_system_allocations


def _set_daily_quota_usages(quotas, logger) -> None:
    for quota in quotas:
        allocation = _get_allocation(quota, logger)
        if allocation is None:
            continue
        allocation.set_usage("storage_quota", quota.get("capacity_usage"))


def _get_allocation(quota, logger) -> Optional[Allocation]:
    path = quota.get("path")
    paths = [path, path[:-1]] if path[-1] == "/" else [path, f"{path}/"]
    allocation = _get_allocation_by_attribute(paths, "storage_filesystem_path", logger)
    return allocation


def _get_allocation_by_attribute(
    values: list[str], attribute_type_name: str, logger
) -> Optional[Allocation]:
    try:
        attribute = AllocationAttribute.objects.select_related("allocation").get(
            value__in=values,
            allocation_attribute_type__name=attribute_type_name,
            allocation__status__name="Active",
        )
    except AllocationAttribute.DoesNotExist:
        logger.warn(f"Allocation record for {','.join(values)} path was not found")
        return None

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
    return (usage / limit) >= get_storage_limit_threshold()
