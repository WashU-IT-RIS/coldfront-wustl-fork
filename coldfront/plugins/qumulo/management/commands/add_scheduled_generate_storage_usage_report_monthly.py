import arrow
from django.core.management.base import BaseCommand

from django_q.tasks import schedule

from django_q.models import Schedule

from datetime import datetime, timezone

from coldfront.plugins.qumulo.reports.storage_usage_report import StorageUsageReport 

from django.core.mail import send_mail

SCHEDULED_FOR_2ND_DAY_OF_MONTH_AT_6_AM = (
    arrow.utcnow().replace(day=2, hour=6, minute=00).format(arrow.FORMAT_RFC3339)
)


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--school', type=str, default='ENG', help='School unit (default: ENG)')
        parser.add_argument('--email', type=str, required=True, help='Recipient email address')

    def handle(self, *args, **options):
        school = options['school']
        email = options['email']
        print(f"Scheduling generating storage2&3 usage report for school {school}...")
        schedule(
            func="coldfront.plugins.qumulo.management.commands.add_scheduled_generate_storage_usage_report_monthly.generate_storage2_3_monthly_usage_report",
            name=f"Generate Storage2&3 Monthly Usage Report for {school}",
            schedule_type=Schedule.MONTHLY,
            next_run=SCHEDULED_FOR_2ND_DAY_OF_MONTH_AT_6_AM,
            args=[school, email],
        )



def generate_storage2_3_monthly_usage_report(
        usage_date=datetime.now(timezone.utc).strftime("%Y-%m-01"),
        school='ENG',
        email='tz-kai.lin@wustl.edu'
    ):
    """
    Generate the Storage2&3 Monthly Usage Report for the given school and email it.
    """
    report_generator = StorageUsageReport(usage_date=usage_date)
    usage_report = report_generator.generate_report_for_school(school)

    subject = f"Storage2&3 Monthly Usage Report for {school}"
    message = f"Here is your monthly storage usage report for {school}:\n\n{usage_report}"
    from_email = 'noreply@gowustl.onmicrosoft.com'
    recipient_list = [email] if email else []

    if recipient_list:
        send_mail(
            subject,
            message,
            from_email,
            recipient_list,
            fail_silently=False,
        )
        print(f"Storage2&3 Monthly Usage Report for {school} has been sent via email to {email}.")
    else:
        print("No recipient email provided. Report not sent.")

