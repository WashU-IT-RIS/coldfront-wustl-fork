import arrow
from coldfront.plugins.qumulo.utils.active_directory_api import ActiveDirectoryAPI
from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttributeUsage,
    AllocationAttribute,
)
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django_q.tasks import schedule
from django_q.models import Schedule
from datetime import datetime, timezone
from coldfront.plugins.qumulo.reports.storage_usage_report import StorageUsageReport 

SCHEDULED_FOR_2ND_DAY_OF_MONTH_AT_6_AM = (
    arrow.utcnow().replace(day=2, hour=6, minute=00).format(arrow.FORMAT_RFC3339)
)


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--project', type=str, default='Genetics Storage 3 Condo', help='Project (default: Genetics Storage 3 Condo)')
        parser.add_argument('--email', type=str, help='Recipient email address')

    def handle(self, *args, **options):
        project = options['project']
        email = options['email']
        print(f"Scheduling to generate storage2&3 monthly usage report to {email} for condo {project}...")
        schedule(
            func="coldfront.plugins.qumulo.management.commands.add_scheduled_generate_storage3_condo_usage_report_monthly.generate_storage3_condo_usage_report",
            name=f"Generate Storage3 Monthly Usage Report for {project}",
            schedule_type=Schedule.MONTHLY,
            next_run=SCHEDULED_FOR_2ND_DAY_OF_MONTH_AT_6_AM,
            project=project,
            email=email,
        )


def generate_storage3_condo_usage_report(
        usage_date = datetime.now(timezone.utc).strftime("%Y-%m-01"),
        project: str = 'Genetics Storage 3 Condo',
        email: str = None,
        **kwargs
    ):
    """
    Generate the Storage3 Monthly Usage Report for the given project and email it.
    """
    print(f"Generating Storage3 Monthly Usage Report for {project} emailing to {email}.")

    report_generator = StorageUsageReport(usage_date=usage_date)
    usage_report = report_generator.generate_report_for_project(project)
    print(usage_report)

    subject = f"Storage3 Monthly Usage Report with consumptions on {usage_date} for {project}"
    message = f"Here is the Storage2&3 usage report with consumptions on {usage_date} for {project} by PIs:\n\n{usage_report}"
    from_email = 'noreply@gowustl.onmicrosoft.com'
    recipient_list = [email] if email else []

    billing_contacts = []
    for allocation in getattr(usage_report, 'allocations', []) or []:
        active_directory_api = ActiveDirectoryAPI()
        billing_contact = allocation.get_attribute("billing_contact")
        billing_contact_email = active_directory_api.get_user(billing_contact)
        if billing_contact_email:
            billing_contacts.append(billing_contact_email)

    recipient_list = list(dict.fromkeys(email for email in billing_contacts if email))
    if not recipient_list and email:
        recipient_list = [email]

    if recipient_list:
        send_mail(
            subject,
            message,
            from_email,
            recipient_list,
            fail_silently=False,
        )
        print(f"Storage3 Monthly Usage Report for {project} with consumptions on {usage_date} has been sent via email to {', '.join(recipient_list)}.")
    else:
        print("No recipient email provided. Report not sent.")

