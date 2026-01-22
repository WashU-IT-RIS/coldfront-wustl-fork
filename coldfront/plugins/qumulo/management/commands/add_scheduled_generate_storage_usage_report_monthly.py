import arrow
from django.core.management.base import BaseCommand

from django_q.tasks import schedule

from django_q.models import Schedule

from datetime import datetime, timezone

from coldfront.plugins.qumulo.reports.storage_usage_report import StorageUsageReport 

SCHEDULED_FOR_2ND_DAY_OF_MONTH_AT_6_AM = (
    arrow.utcnow().replace(day=2, hour=6, minute=00).format(arrow.FORMAT_RFC3339)
)


class Command(BaseCommand):

    def handle(self, *args, **options):
        print("Scheduling generating storage2&3 usage report for school of Engineering...")
        schedule(
            func="coldfront.plugins.qumulo.management.commands.add_scheduled_generate_storage_usage_report_monthly.generate_storage2_monthly_billing_report",
            name="Generate Storage2 Monthly Billing Report",
            schedule_type=Schedule.MONTHLY,
            next_run=SCHEDULED_FOR_2ND_DAY_OF_MONTH_AT_6_AM,
        )


def generate_storage2_3_monthly_usage_report() -> None:
    storage_report = StorageUsageReport(datetime.now(timezone.utc).strftime("%Y-%m-01"))
    storage_report.generate_report_for_school('ENG')