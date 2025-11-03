import arrow
from django.core.management.base import BaseCommand

from django_q.tasks import schedule

from django_q.models import Schedule

from datetime import datetime, timezone

SCHEDULED_FOR_2ND_DAY_OF_MONTH_AT_3_00_AM = (
    arrow.utcnow().replace(day=2, hour=3, minute=0).format(arrow.FORMAT_RFC3339)
)


class Command(BaseCommand):

    def handle(self, *args, **options):
        print("Scheduling generating integrated monthly billing report")
        schedule(
            func="coldfront.plugins.integratedbilling.management.commands.add_schedule_for_integrated_billing_reports.generate_integrated_billing_report",
            name="Generate Integrated Monthly Billing Report",
            schedule_type=Schedule.MONTHLY,
            next_run=SCHEDULED_FOR_2ND_DAY_OF_MONTH_AT_3_00_AM,
        )


def generate_integrated_billing_report() -> None:
    from coldfront.plugins.integratedbilling.report_generator import ReportGenerator   

    usage_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    report_generator = ReportGenerator(usage_date)
    success = report_generator.generate()
    print("Integrated Monthly Billing Report generation success:", success)
