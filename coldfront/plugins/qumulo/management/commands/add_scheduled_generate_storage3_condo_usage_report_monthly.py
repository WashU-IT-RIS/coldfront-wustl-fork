import arrow
from coldfront.plugins.qumulo.utils.active_directory_api import ActiveDirectoryAPI
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django_q.tasks import schedule
from django_q.models import Schedule
from datetime import datetime, timezone
from coldfront.core.utils.common import import_from_settings
from coldfront.plugins.qumulo.reports.storage_usage_report import (
    NO_USAGE_DATA,
    StorageUsageReport,
)

REPORT_FUNC = "coldfront.plugins.qumulo.management.commands.add_scheduled_generate_storage3_condo_usage_report_monthly.generate_storage3_condo_usage_report"
FAILURE_HOOK = "coldfront.plugins.qumulo.hooks.notify_on_call_on_failure_hook"
# The report does one Active Directory lookup per billing contact, so give it
# more time than the cluster default (120s). A timed-out task is killed without
# being recorded as failed, so it would never reach the failure hook.
REPORT_TIMEOUT_SECONDS = 600

EMAIL_DEVELOPMENT_EMAIL_LIST = import_from_settings("EMAIL_DEVELOPMENT_EMAIL_LIST", [])


def next_run_on_2nd_at_6_am_utc(now: arrow.Arrow = None) -> str:
    """The next 2nd of the month at 06:00 UTC that is still in the future."""
    now = now or arrow.utcnow()
    next_run = now.replace(day=2, hour=6, minute=0, second=0, microsecond=0)
    if next_run <= now:
        next_run = next_run.shift(months=+1)
    return next_run.format(arrow.FORMAT_RFC3339)


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--project', type=str, default='Genetics Storage 3 Condo', help='Project (default: Genetics Storage 3 Condo)')
        parser.add_argument(
            '--dry-run',
            help='Schedule the report to be generated and logged each month without emailing it.',
        )

    def handle(self, *args, **options):
        project = options['project']
        dry_run = options['dry_run']
        name = f"Generate Storage3 Monthly Usage Report for {project}"

        # Re-running the command replaces the schedule instead of adding a
        # second one, which would email every billing contact twice a month.
        deleted, _ = Schedule.objects.filter(name=name, func=REPORT_FUNC).delete()
        if deleted:
            print(f"Replacing {deleted} existing schedule(s) named '{name}'.")

        next_run = next_run_on_2nd_at_6_am_utc()
        dry_run_note = " (dry run: the report will not be emailed)" if dry_run else ""
        print(f"Scheduling to generate storage 3 monthly usage report for condo {project}, first run at {next_run}{dry_run_note}...")
        schedule(
            func=REPORT_FUNC,
            name=name,
            schedule_type=Schedule.MONTHLY,
            next_run=next_run,
            hook=FAILURE_HOOK,
            q_options={"timeout": REPORT_TIMEOUT_SECONDS},
            project=project,
            dry_run=dry_run,
        )


def generate_storage3_condo_usage_report(
        usage_date: str = None,
        project: str = 'Genetics Storage 3 Condo',
        dry_run: bool = False,
        **kwargs
    ):
    """
    Generate the Storage3 Monthly Usage Report for the given project and email it.
    usage_date defaults to the 1st of the current month, computed at call time.
    With dry_run, the report and its recipients are logged but no email is sent.
    Raises if no allocation has usage recorded on usage_date, so the failure
    hook alerts on-call instead of an empty report going to billing contacts.
    """
    if usage_date is None:
        usage_date = datetime.now(timezone.utc).strftime("%Y-%m-01")
    print(f"Generating Storage3 Monthly Usage Report for {project}.")

    report_generator = StorageUsageReport(usage_date=usage_date)
    usages = report_generator.get_usages_for_project(project)
    if all(usage["usage_kb"] == NO_USAGE_DATA for usage in usages):
        raise ValueError(
            f"No usage data recorded on {usage_date} for any of the {len(usages)} "
            f"active allocation(s) in {project}. Check the daily usage ingestion. "
            "Report not sent."
        )

    usage_report = report_generator.generate_report_for_project(project)
    print(usage_report)

    subject = f"Storage3 Monthly Usage Report with consumptions on {usage_date} for {project}"
    message = f"Here is the Storage 3 usage report with consumptions on {usage_date} for {project}:\n\n{usage_report}"

    allocations = report_generator.get_allocations_by_project(project)
    recipient_list = get_billing_contact_emails(allocations)

    if not recipient_list:
        print("No billing contact emails found. Report not sent.")
        return

    # Outside production, send to the developers instead of real billing contacts.
    if settings.DEBUG:
        recipient_list = EMAIL_DEVELOPMENT_EMAIL_LIST

    if dry_run:
        print(f"Dry run: report not sent to {', '.join(recipient_list)}.")
        return

    # Not the send_email helper: it swallows SMTP errors, and a failed send must
    # raise so the failure hook alerts on-call.
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        recipient_list,
        fail_silently=False,
    )
    print(f"Storage3 Monthly Usage Report for {project} with consumptions on {usage_date} has been sent via email to {', '.join(recipient_list)}.")


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

