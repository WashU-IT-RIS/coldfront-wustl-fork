import arrow
from datetime import datetime, timezone

from django.core.management.base import BaseCommand
from django_q.tasks import schedule
from django_q.models import Schedule

from coldfront.plugins.integratedbilling.report_generator import ReportGenerator

SCHEDULED_FOR_2ND_DAY_OF_MONTH_AT_3_00_AM = (
    arrow.now().replace(day=2, hour=3, minute=0).format(arrow.FORMAT_RFC3339)
)


class Command(BaseCommand):

    def handle(self, *args, **options) -> None:
        print("Scheduling task for generating integrated billing report monthly...")
        schedule(
            func="coldfront.plugins.integratedbilling.management.commands.add_schedule_for_integrated_billing_reports.generate_integrated_billing_report",
            name="Generate Integrated Monthly Billing Report",
            schedule_type=Schedule.MONTHLY,
            next_run=SCHEDULED_FOR_2ND_DAY_OF_MONTH_AT_3_00_AM,
        )
        return None


def generate_integrated_billing_report() -> None:
    usage_date = datetime.now(tz=timezone.utc).replace(
        day=1, hour=6, minute=0, second=0, microsecond=0
    )

    report_generator = ReportGenerator(usage_date)
    success = report_generator.generate()
    print("Integrated Monthly Billing Report generation success: ", success)
    return None
