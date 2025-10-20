from typing import Union
from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttribute,
    AllocationAttributeUsage,
)
from django.db.models.query import QuerySet
from django.db.models.expressions import OuterRef, Star, Subquery
from datetime import date

from coldfront.core.billing.models import AllocationUsage
from coldfront.core.service_rate_category.models import Service
from coldfront.plugins.integratedbilling.constants import BillingDataSources


class ColdfrontUsageIngestor:

    def __init__(self, usage_date: date):
        self.usage_date = usage_date
        self.service = Service.objects.get(name="Storage2")
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

    def __ingest_usage_data(self, usage_date: date) -> QuerySet:
        sub_queries = self.__get_subqueries(usage_date)
        active_allocations_with_usage = (
            Allocation.objects.parents()
            .active_storage()
            .consumption()
            .annotate(**sub_queries)
            .filter(usage_bytes__isnull=False)
        )

        return active_allocations_with_usage

    def __create_allocation_usage_records(
        self, active_allocations_with_usages: QuerySet
    ) -> list[AllocationUsage]:
        usage_records = []
        for allocation_with_usage in active_allocations_with_usages:
            amount_tb = self.__convert_to_amount_usage_to_tb(
                allocation_with_usage.usage_bytes
            )
            record = AllocationUsage(
                external_key=allocation_with_usage.pk,
                source=self.source,
                sponsor_pi=allocation_with_usage.sponsor_pi,
                billing_contact=allocation_with_usage.billing_contact,
                fileset_name=allocation_with_usage.fileset_name,
                service_rate_category=allocation_with_usage.service_rate_category,
                usage_tb=amount_tb,
                funding_number=allocation_with_usage.funding_number,
                exempt=allocation_with_usage.billing_exempt,
                subsidized=allocation_with_usage.subsidized,
                is_condo_group=allocation_with_usage.is_condo_group,
                parent_id_key=allocation_with_usage.parent_id_key,
                quota=allocation_with_usage.quota,
                billing_cycle=allocation_with_usage.billing_cycle,
                usage_date=self.usage_date,
                storage_cluster=self.service.name,
            )

            usage_records.append(record)
        return usage_records

    def __convert_to_amount_usage_to_tb(self, amount_bytes: int) -> Union[float, None]:
        try:
            amount_tb = float(amount_bytes) / 1_000_000_000_000  # 1024**4 perhaps
            return round(amount_tb, 6)
        except (TypeError, ValueError):
            return None

    def __get_subqueries(self, usage_date: date = None) -> dict:
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
                    history_date__date=usage_date,
                ).values("value")
            )
            sub_queries["usage_bytes"] = usage_subquery

        return sub_queries
