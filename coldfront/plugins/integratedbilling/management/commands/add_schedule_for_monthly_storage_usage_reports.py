import arrow
import os
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
        print(f"Scheduling to generate Monthly Storage Usage Reports to {email}...")
        schedule(
            func="coldfront.plugins.integratedbilling.management.commands.add_schedule_for_monthly_storage_usage_reports.generate_monthly_storage_usage_reports",
            name="Generate Monthly Storage Usage Reports",
            schedule_type=Schedule.MONTHLY,
            next_run=SCHEDULED_FOR_2ND_DAY_OF_MONTH_AT_6_AM,
            email=email,
        )


def generate_monthly_storage_usage_reports(
    usage_date=datetime.now(timezone.utc).replace(day=1).date(),
    email: str = None,
    **kwargs,
):
    """
    Generate the Monthly Storage Usage Reports and email them.
    """
    usage_date_str = usage_date.strftime("%Y-%m-%d")
    print(
        f"Generating Monthly Storage Usage Reports with consumptions on {usage_date_str} for emailing to {email}."
    )

    file = list()
    for tier in [ServiceTiers.Active, ServiceTiers.Archive]:
        report_agent = StorageUsageReport(usage_date=usage_date, tier=tier)
        filename = f"storage_{tier.name.lower()}_usage_report_{usage_date_str.replace('-', '')}.csv"
        filepath = os.path.join("/tmp", filename)
        report_agent.generate_report(filename=filepath)
        if os.path.exists(filepath):
            file.append(filepath)

    email = EmailMessage(
        subject=f"Monthly Storage Usage Reports with consumptions on {usage_date_str}",
        body=f"Here are the Monthly Storage Usage reports with consumptions on {usage_date_str} by department per PIs.",
        to=[email] if email else [],
    )
    for filepath in file:
        email.attach_file(filepath)
    if email.to:
        email.send(fail_silently=False)
        print(
            f"Monthly Storage Usage Reports with consumptions on {usage_date_str} have been sent via email to {email.to}."
        )
    else:
        print("No recipient email provided. Report not sent.")
