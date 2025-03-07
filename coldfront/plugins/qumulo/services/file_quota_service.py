from datetime import datetime
from coldfront.core.allocation.models import (
    AllocationAttribute,
    AllocationAttributeType,
    AllocationAttributeUsage,
    AllocationStatusChoice,
)
from coldfront.plugins.qumulo.utils.acl_allocations import AclAllocations
from coldfront.plugins.qumulo.utils.qumulo_api import QumuloAPI


class FileQuotaService:

    @staticmethod
    def ingest_quotas_with_daily_usage(logger) -> None:
        base_allocation_quota_usages = FileQuotaService._get_allocation_file_quotas()
        FileQuotaService._set_daily_quota_usages(base_allocation_quota_usages, logger)
        FileQuotaService._validate_results(base_allocation_quota_usages, logger)

    @staticmethod
    def _get_allocation_file_quotas() -> list:
        qumulo_api = QumuloAPI()
        quota_usages = qumulo_api.get_all_quotas_with_usage()["quotas"]
        base_allocation_quota_usages = list(
            filter(
                lambda quota_usage: AclAllocations.is_base_allocation(
                    quota_usage["path"]
                ),
                quota_usages,
            )
        )
        return base_allocation_quota_usages

    @staticmethod
    def _set_daily_quota_usages(quotas, logger) -> None:
        # Iterate and populate allocation_attribute_usage records
        storage_filesystem_path_attribute_type = AllocationAttributeType.objects.get(
            name="storage_filesystem_path"
        )
        active_status = AllocationStatusChoice.objects.get(name="Active")

        for quota in quotas:
            path = quota.get("path")

            allocation = FileQuotaService._get_allocation_by_attribute(
                storage_filesystem_path_attribute_type, path, active_status, logger
            )
            if allocation is None:
                if path[-1] != "/":
                    continue

                value = path[:-1]
                logger.warn(
                    f"Attempting to find allocation without the trailing slash..."
                )
                allocation = FileQuotaService._get_allocation_by_attribute(
                    storage_filesystem_path_attribute_type, value, active_status, logger
                )
                if allocation is None:
                    continue

            allocation.set_usage("storage_quota", quota.get("capacity_usage"))

    @staticmethod
    def _get_allocation_by_attribute(attribute_type, value, for_status, logger):
        try:
            attribute = AllocationAttribute.objects.select_related("allocation").get(
                value=value,
                allocation_attribute_type=attribute_type,
                allocation__status=for_status,
            )
        except AllocationAttribute.DoesNotExist:
            logger.warn(f"Allocation record for {value} path was not found")
            return None

        logger.warn(f"Allocation record for {value} path was found")
        return attribute.allocation

    @staticmethod
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
