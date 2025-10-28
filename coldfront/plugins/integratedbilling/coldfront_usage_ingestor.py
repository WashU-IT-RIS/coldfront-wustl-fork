from typing import Union

from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttribute,
    AllocationAttributeUsage,
)
from django.db.models.query import QuerySet
from django.db.models.expressions import OuterRef, Subquery
from datetime import date, datetime, timezone

from coldfront.core.billing.models import AllocationUsage
from coldfront.plugins.integratedbilling.constants import BillingDataSources


# helper function to get the default billing date (first day of the current month)
def _get_default_usage_date() -> date:
    today = datetime.now()
    return today.replace(
        day=1, hour=18, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
    ).date()


class ColdfrontUsageIngestor:

    def __init__(self, usage_date: datetime = None) -> None:
        self.usage_date = usage_date or _get_default_usage_date()
        self.source = BillingDataSources.COLDFRONT.value

    def process_usages(self) -> bool:
        active_allocations_with_usages = self.__ingest_usage_data(self.usage_date)
        if not active_allocations_with_usages:
            return False

        created_usages = self.__create_allocation_usage_records(
            active_allocations_with_usages
        )

        if not created_usages:
            return False

        return True

    def __ingest_usage_data(self, usage_date: datetime) -> QuerySet:
        sub_queries = self.__get_subqueries(usage_date)
        active_allocations_with_usages = (
            Allocation.objects.parents()
            .active_storage()
            .consumption()
            .annotate(**sub_queries)
            .select_related("project__pi")
        )
        return active_allocations_with_usages

    def __create_allocation_usage_records(
        self, active_allocations_with_usages: QuerySet
    ) -> list[AllocationUsage]:
        saved_usages = []
        for allocation_with_usage in active_allocations_with_usages:
            amount_tb = self.__convert_to_amount_usage_to_tb(
                allocation_with_usage.usage_bytes
            )
            record = AllocationUsage.objects.update_or_create(
                external_key=allocation_with_usage.pk,
                source=self.source,
                usage_date=self.usage_date.date(),
                defaults={
                    "sponsor_pi": allocation_with_usage.project.pi,
                    "billing_contact": allocation_with_usage.billing_contact,
                    "fileset_name": allocation_with_usage.storage_filesystem_path,
                    "service_rate_category": allocation_with_usage.service_rate_category,
                    "usage_tb": amount_tb,
                    "funding_number": allocation_with_usage.funding_number
                    or "NOT PROVIDED",
                    "exempt": self.__to_boolean(
                        allocation_with_usage.billing_exempt, default=None
                    ),
                    "subsidized": self.__to_boolean(
                        allocation_with_usage.subsidized, default=None
                    ),
                    "is_condo_group": self.__to_boolean(
                        allocation_with_usage.is_condo_group
                    ),
                    "parent_id_key": None,
                    "quota": allocation_with_usage.storage_quota,
                    "billing_cycle": allocation_with_usage.billing_cycle,
                    "storage_cluster": allocation_with_usage.resources.filter(
                        name__startswith="Storage"
                    )
                    .first()
                    .name,
                },
            )
            saved_usages.append(record)

        return saved_usages

    def __convert_to_amount_usage_to_tb(self, amount_bytes: int) -> Union[float, None]:
        try:
            amount_tb = float(amount_bytes) / 1_000_000_000_000  # 1024**4 perhaps
            return round(amount_tb, 6)
        except (TypeError, ValueError):
            return None

    def __to_boolean(self, value: str, default: bool = False) -> bool:
        if str(value) in ["Yes", "True", "true", "1"]:
            return True
        if str(value) in ["No", "False", "false", "0"]:
            return False
        return default

        return None

    def __get_subqueries(self, usage_date: datetime) -> dict:
        sub_queries = {}
        for key in [
            "storage_filesystem_path",
            "is_condo_group",
            "billing_contact",
            "service_rate_category",
            "funding_number",
            "billing_exempt",
            "subsidized",
            "storage_quota",
            "billing_cycle",
        ]:
            sub_queries[key] = Subquery(
                AllocationAttribute.objects.filter(
                    allocation=OuterRef("pk"),
                    allocation_attribute_type__name=key,
                ).values("value")[:1]
            )
            usage_subquery = Subquery(
                AllocationAttributeUsage.history.filter(
                    allocation_attribute__allocation=OuterRef("pk"),
                    allocation_attribute__allocation_attribute_type__name="storage_quota",
                    history_date=usage_date,
                ).values("value")
            )
            sub_queries["usage_bytes"] = usage_subquery

        return sub_queries
