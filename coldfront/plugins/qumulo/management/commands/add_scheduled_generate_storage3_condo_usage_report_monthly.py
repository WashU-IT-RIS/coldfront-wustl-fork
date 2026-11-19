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
    message = f"Here is the Storage 3 usage report with consumptions on {usage_date} for {project} by PIs:\n\n{usage_report}"
    from_email = 'noreply@gowustl.onmicrosoft.com'

    allocations = report_generator.get_allocations_by_project(project)
    recipient_list = get_billing_contact_emails(allocations)

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
        print("No billing contact emails found. Report not sent.")


def get_billing_contact_emails(allocations) -> list[str]:
    """
    Look up the email address of each allocation's billing contact in Active Directory.
    Returns unique addresses in allocation order; contacts that can't be found are skipped.
    """
    active_directory_api = ActiveDirectoryAPI()
    emails = []
    for allocation in allocations:
        billing_contact = allocation.get_attribute("billing_contact")
        if not billing_contact:
            print(f"Allocation {allocation.pk} has no billing contact; skipping.")
            continue
        try:
            mail = active_directory_api.get_user(billing_contact)["attributes"]["mail"]
        except (ValueError, KeyError) as error:
            print(f"Could not find an email for billing contact {billing_contact} of allocation {allocation.pk}: {error}")
            continue
        # ldap3 can return a single-valued attribute as a list
        if isinstance(mail, list):
            mail = mail[0] if mail else None
        if mail and mail not in emails:
            emails.append(mail)
    return emails

