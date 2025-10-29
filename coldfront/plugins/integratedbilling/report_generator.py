import json
from coldfront.core.billing.models import AllocationUsage
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
        # filtered_allocation_usages.set_and_validate_all_subsidized()

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

    def __save_report(self, report_data, file_path):
        with open(file_path, "w") as file:
            json.dump(report_data, file, indent=4)
            file.close()

    def __log_report_generation(self, status, details):
        print(f"Report Generation Status: {status}, Details: {details}")

    def __generate_summary(self, usages):
        summary = {
            "total_usages": usages.count(),
            "total_amount_tb": sum(usage.usage_tb for usage in usages),
            "total_subsidized": sum(1 for usage in usages if usage.subsidized),
        }
        return summary

    def __calculate_usage_cost(self, usages: AllocationUsage) -> list:
        calculated_costs = []
        for usage in usages:
            rate_category = ServiceRateCategory.current.for_model(
                usage
            ).first()
            if rate_category:
                cost = usage.usage_tb * rate_category.rate
            else:
                cost = 0
            calculated_costs.append(
                {
                    "allocation_id": usage.allocation_id,
                    "usage_tb": usage.usage_tb,
                    "cost": cost,
                }
            )
        return calculated_costs