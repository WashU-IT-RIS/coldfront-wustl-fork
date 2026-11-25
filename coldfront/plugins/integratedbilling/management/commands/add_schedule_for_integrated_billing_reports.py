import arrow
from datetime import datetime, timezone

from django.core.management.base import BaseCommand
from django_q.models import Schedule

from coldfront.plugins.integratedbilling.constants import ServiceTiers
from coldfront.plugins.integratedbilling.report_generator import ReportGenerator

_30_MINUTES_IN_SECONDS = 1800


def _next_2nd_day_of_month_at_3_00_am() -> str:
    now = arrow.now()
    next_run = now.replace(day=2, hour=3, minute=0, second=0, microsecond=0)
    if next_run <= now:
        next_run = next_run.shift(months=1)
    return next_run.format(arrow.FORMAT_RFC3339)


class Command(BaseCommand):

    def handle(self, *args, **options) -> None:
        print("Scheduling task for generating integrated billing report monthly...")
        # django-q 1.3.9's Schedule has no q_options field; per-task options are
        # read from the `kwargs` text field. Only `timeout` is per-task: `retry`
        # is cluster-wide (Q_CLUSTER_RETRY). It has no effect on the default
        # Redis broker, but on the ORM/SQS/Mongo brokers it must be set above
        # this timeout or the task will be redelivered while still running.
        Schedule.objects.update_or_create(
            name="Generate Integrated Monthly Billing Report",
            defaults={
                "func": "coldfront.plugins.integratedbilling.management.commands.add_schedule_for_integrated_billing_reports.generate_integrated_billing_report",
                "schedule_type": Schedule.MONTHLY,
                "next_run": _next_2nd_day_of_month_at_3_00_am(),
                "kwargs": f"q_options={{'timeout': {_30_MINUTES_IN_SECONDS}}}",
            },
        )


def generate_integrated_billing_report() -> None:
    usage_date = datetime.now(tz=timezone.utc).replace(
        day=1, hour=18, minute=0, second=0, microsecond=0
    )
    __generate_integrated_billing_report_for(ServiceTiers.Active, usage_date)
    __generate_integrated_billing_report_for(ServiceTiers.Archive, usage_date)


def __generate_integrated_billing_report_for(
    tier: ServiceTiers, usage_date: datetime
) -> None:
    active_storage_report_generator = ReportGenerator(usage_date=usage_date, tier=tier)
    success = active_storage_report_generator.generate()
    print(
        f"Integrated Monthly {tier.name} Storage Billing Report generation success: ",
        success,
    )
