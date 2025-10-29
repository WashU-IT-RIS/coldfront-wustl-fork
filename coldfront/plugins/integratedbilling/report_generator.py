import json
from coldfront.core.billing.models import AllocationUsage, MonthlyStorageBilling
from coldfront.plugins.integratedbilling.coldfront_usage_ingestor import (
    ColdfrontUsageIngestor,
)
from coldfront.plugins.integratedbilling.billing_itsm_client import BillingItsmClient
from coldfront.plugins.integratedbilling.itsm_usage_ingestor import (
    ItsmUsageIngestor,
)
from coldfront.plugins.integratedbilling.models import ServiceRateCategory


class ReportGenerator:

    def __init__(self, usage_date=None):
        self.client = BillingItsmClient(usage_date)
        self.itsm_usage_ingestion = ItsmUsageIngestor(self.client)
        self.coldfront_usage_ingestion = ColdfrontUsageIngestor(usage_date)

    def generate(self, ingest_usages=True) -> None:
        if ingest_usages:
            success = self.itsm_usage_ingestion.process_usages()
            if not success:
                return False

            success = self.coldfront_usage_ingestion.process_usages()
            if not success:
                return False

        # get usages for month and filter as needed
        filtered_allocation_usages = self.__get_allocation_usages()

        # set the subsidies if applicable
        filtered_allocation_usages.set_and_validate_all_subsidized()

        # calculate costs
        calculated_usage_costs = self.__calculate_usage_cost(filtered_allocation_usages)

        self.__save_report(
            calculated_usage_costs, f"billing_report_{self.client.usage_date}.csv"
        )
        self.__send_report(calculated_usage_costs)

        summary = self.__generate_summary(filtered_allocation_usages)
        self.__log_report_generation(status="Success", details=summary)
        return True

    # Private methods
    def __get_allocation_usages(self):
        monthly_usages = AllocationUsage.objects.monthly_billable(
            self.client.usage_date,
        )
        return monthly_usages

    def __send_report(self, report_data):
        print("Report not sent since this is a placeholder method.")

    def __save_report(self, billing_objects: list, file_path: str) -> None:
        MonthlyStorageBilling.generate_report(billing_objects, None, file_path)

    def __log_report_generation(self, status: str, details: dict) -> None:
        print(f"Report Generation Status: {status}, Details: {details}")

    def __generate_summary(self, usages) -> dict:
        summary = {
            "total_usages": usages.count(),
            "total_amount_tb": sum(usage.usage_tb for usage in usages),
            "total_subsidized": sum(1 for usage in usages if usage.subsidized),
        }
        return summary

    def __calculate_usage_cost(self, usages) -> list:
        billing_objects = []
        for billing_object in usages:
            tier_name = "active"  # billing_object.tier_name
            model_name = billing_object.service_rate_category
            billing_cycle = billing_object.billing_cycle
            print(
                f"Calculating cost for Usage ID {billing_object.id}: Tier={tier_name}, Model={model_name}, Cycle={billing_cycle}"
            )
            rate_category = (
                ServiceRateCategory.current_rates.all()
                .for_tier(tier_name)
                .for_cycle(billing_cycle)
                .get()
            )
            if rate_category:
                billing_object.calculated_cost = (
                    billing_object.usage_tb * rate_category.rate
                )
            else:
                billing_object.calculated_cost = 0

            billing_object.delivery_date = "2024-05-01"  # (str): indicates the beginning date of the service for monthly billing (ex. 2024-05-01)
            billing_object.tier = (
                rate_category.tier_name
            )  # (str): indicates the service tier of the allocation (ex. Active, Archive)
            billing_object.billing_unit = (
                rate_category.unit
            )  # (str): indicates the billing unit of the service (ex. TB)
            billing_object.unit_rate = (
                rate_category.rate
            )  # (str): indicates the unit rate of the service
            billing_object.billing_amount = (
                billing_object.calculated_cost
            )  # (str): indicates the total dollar amount of the service for the monthly billing
            billing_objects.append(billing_object)
        breakpoint()
        return billing_objects
