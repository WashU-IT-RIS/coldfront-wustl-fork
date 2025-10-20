from coldfront.core.billing.models import AllocationUsage


class ReportFormatter:

    # this is just an example method
    def format_report_data(self, usages: list[AllocationUsage]) -> list[dict]:
        print("Formatting report data...")
        report_data = []
        # Sample formatter logic; TBD by Kevin
        for usage in usages:
            report_entry = {
                "date": usage.usage_date.strftime("%Y-%m-%d"),
                "storage_cluster": usage.storage_cluster,
                "usage_tb": str(usage.usage_tb),
            }
            report_data.append(report_entry)
        return report_data
