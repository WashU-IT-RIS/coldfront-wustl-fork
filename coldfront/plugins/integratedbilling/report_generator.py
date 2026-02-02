from datetime import date, datetime, timedelta, timezone

from coldfront.plugins.integratedbilling.constants import ServiceTiers
from coldfront.core.billing.models import AllocationUsage, MonthlyStorageBilling
from coldfront.plugins.integratedbilling.coldfront_usage_ingestor import (
    ColdfrontUsageIngestor,
)
from coldfront.plugins.integratedbilling.billing_itsm_client import BillingItsmClient
from coldfront.plugins.integratedbilling.itsm_usage_ingestor import (
    ItsmUsageIngestor,
)
from coldfront.plugins.integratedbilling.fee_calculator import get_billing_objects


class ReportGenerator:
    def __init__(
        self,
        usage_date: datetime = None,
        delivery_date: datetime = None,
        tier: ServiceTiers = ServiceTiers.Active,
    ) -> None:
        self.usage_date = (usage_date or _get_default_usage_date()).date()
        self.client = BillingItsmClient(usage_date, tier)
        self.itsm_usage_ingestion = ItsmUsageIngestor(self.client)
        self.coldfront_usage_ingestion = ColdfrontUsageIngestor(usage_date)
        self.tier = tier
        self.delivery_date = delivery_date or self.__get_delivery_date()
        self.delivery_month = self.delivery_date.strftime("%B")

    def generate(self, ingest_usages=True, dry_run=False) -> bool:
        if ingest_usages:
            success = self.itsm_usage_ingestion.process_usages()
            if not success:
                return False

            self.coldfront_usage_ingestion.process_usages()

        filtered_allocation_usages = self.__get_allocation_usages()

        if not self.__handle_subsidies(filtered_allocation_usages):
            return False

        calculated_usage_costs = self.__calculate_usage_fee(filtered_allocation_usages)

        self.__save_report(calculated_usage_costs)
        summary = self.__generate_summary(filtered_allocation_usages)
        self.__log_report_generation(status="Success", details=summary)

        # do not send report if dry run
        if dry_run:
            return False

        self.__send_report(calculated_usage_costs)

        return True

    # Private methods
    def __get_allocation_usages(self) -> list[AllocationUsage]:
        monthly_usages = AllocationUsage.objects.monthly_billable(
            usage_date=self.usage_date,
            tier=self.tier.name,
        )
        return monthly_usages

    def __calculate_usage_fee(
        self, usages: list[AllocationUsage]
    ) -> list[MonthlyStorageBilling]:
        billing_objects = get_billing_objects(usages, self.delivery_date)
        return billing_objects

    def __save_report(self, billing_objects: list, file_path: str = None) -> None:
        file_path = file_path or self.__get_report_file_name()
        MonthlyStorageBilling.generate_report(billing_objects, output_path=file_path)

    def __log_report_generation(self, status: str, details: dict) -> None:
        print(f"Report Generation Status: {status}, Details: {details}")

    def __generate_summary(self, usages) -> dict:
        summary = {
            "total_usages": usages.count(),
            "total_amount_tb": sum(usage.usage_tb for usage in usages),
            "total_subsidized": sum(1 for usage in usages if usage.subsidized),
        }
        return summary

    def __send_report(self, report_data):
        print("Report not sent since the implementation is pending.")

    def __get_delivery_date(self) -> date:
        first_of_previous_month = (
            self.usage_date.replace(day=1) - timedelta(days=1)
        ).replace(day=1)
        return first_of_previous_month

    def __get_report_file_name(self) -> str:
        return f"/tmp/RIS-{self.delivery_month}-storage-{self.tier.name.lower()}-billing.csv"

    def __handle_subsidies(
        self, filtered_allocation_usages: list[AllocationUsage]
    ) -> None:
        result = filtered_allocation_usages.set_and_validate_all_subsidized()
        if not result:
            self.__log_failed_subsidized_entries(filtered_allocation_usages)
            return False
        else:
            return True

    def __log_failed_subsidized_entries(self, billable_alloc_usages):
        # Find PIs and allocations when the PI has more than one subsidized allocation
        pis = billable_alloc_usages.values_list('sponsor_pi', flat=True).order_by().distinct()
        for pi in pis:
            if not billable_alloc_usages._is_subsidized_valid_by_pi(pi):
                print(f"[Subsidized Validation Failure] PI {pi} has multiple subsidized allocations.")
                for usage in billable_alloc_usages.filter(sponsor_pi=pi):
                    print(f"    Allocation: source={usage.source}, external_key={usage.external_key}, filesystem_path={usage.filesystem_path}, exempt={usage.exempt}, subsidized={usage.subsidized}")


# helper function to get the default billing date (first day of the current month)
def _get_default_usage_date() -> datetime:
    today = datetime.now(tz=timezone.utc)
    return today.replace(day=1, hour=18, minute=0, second=0, microsecond=0)
