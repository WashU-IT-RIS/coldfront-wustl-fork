import arrow
from django.core.management.base import BaseCommand
from django.core.mail import send_mail, EmailMessage
from django_q.tasks import schedule
from django_q.models import Schedule
from datetime import datetime, timezone
from coldfront.plugins.integratedbilling.storage_usage_report import StorageUsageReport
from coldfront.plugins.integratedbilling.constants import ServiceTiers

SCHEDULED_FOR_2ND_DAY_OF_MONTH_AT_6_AM = (
    arrow.utcnow().replace(day=2, hour=6, minute=00).format(arrow.FORMAT_RFC3339)
)


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("--email", type=str, help="Recipient email address")

    def handle(self, *args, **options):
        email = options["email"]
        print(f"Scheduling to generate Monthly Storage Usage Report to {email}...")
        schedule(
            func="coldfront.plugins.integratedbilling.management.commands.add_schedule_for_monthly_storage_usage_report.generate_monthly_storage_usage_report",
            name="Generate Monthly Storage Usage Report",
            schedule_type=Schedule.MONTHLY,
            next_run=SCHEDULED_FOR_2ND_DAY_OF_MONTH_AT_6_AM,
            email=email,
        )


def generate_monthly_storage_usage_report(
    usage_date=datetime.now(timezone.utc).replace(day=1).date(),
    email: str = None,
    **kwargs,
):
    """
    Generate the Monthly Storage Usage Report and email it.
    """
    usage_date_str = usage_date.strftime("%Y-%m-%d")
    print(
        f"Generating Monthly Storage Usage Report with consumptions on {usage_date_str} for emailing to {email}."
    )

    for tier in [ServiceTiers.Active, ServiceTiers.Archive]:
        report_agent = StorageUsageReport(usage_date=usage_date, tier=tier)
        usage_report = report_agent.generate_report()
        usage_report = f"{usage_report}\n\n"

    subject = f"Monthly Storage Usage Report with consumptions on {usage_date_str}"
    message = f"Here is the Monthly Storage Usage report with consumptions on {usage_date_str} by department per PIs:\n\n{usage_report}"
    from_email = "noreply@gowustl.onmicrosoft.com"
    recipient_list = [email] if email else []

    if recipient_list:
        send_mail(
            subject,
            message,
            from_email,
            recipient_list,
            fail_silently=False,
        )
        print(
            f"Monthly Storage Usage Report with consumptions on {usage_date_str} has been sent via email to {email}."
        )
    else:
        print("No recipient email provided. Report not sent.")
