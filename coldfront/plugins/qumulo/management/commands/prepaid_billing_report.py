from django.core.management.base import BaseCommand

from django_q.tasks import schedule

from django_q.models import Schedule

from coldfront.plugins.qumulo.utils.eib_billing import PrepaidBilling


class Command(BaseCommand):

    def handle(self, *args, **options):
        print("Scheduling generating storage2 monthly billing report")
        schedule(
            "coldfront.plugins.qumulo.management.commands.prepaid_billing_report.generate_prepaid_billing_report",
            name="Generate Prepaid Billing Report",
            schedule_type=Schedule.DAILY,
        )


def generate_prepaid_billing_report() -> None:
    prepaid_billing = PrepaidBilling()
    prepaid_billing.generate_prepaid_billing_report()
