from django.core.management.base import BaseCommand
import logging

from django_q.models import Schedule

from coldfront.plugins.qumulo.tasks import (
    poll_ad_groups,
    conditionally_update_storage_allocation_statuses,
)

from coldfront.plugins.qumulo.management.commands.check_billing_cycles import (
    check_allocations,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("Scheduling AD Poller")
        Schedule.objects.get_or_create(
            func="coldfront.plugins.qumulo.management.commands.add_scheduled_ad_poller.sequential_poll_and_check",
            name="Update Pending Allocations",
            schedule_type=Schedule.MINUTES,
            minutes=1,
            repeats=-1,
        )
        print("Scheduling Prepaid Expiration Date Scanner")
        Schedule.objects.get_or_create(
            func="coldfront.plugins.qumulo.management.commands.add_scheduled_ad_poller.prepaid_expiration_cleanup",
            name="Check Billing Statuses",
            schedule_type=Schedule.MINUTES,
            minutes=1,
            repeats=-1,
        )


def sequential_poll_and_check() -> None:
    poll_ad_groups()
    conditionally_update_storage_allocation_statuses()


def prepaid_expiration_cleanup() -> None:
    logger.warn(f"Calling conditionally_update_billing_cycle_type")
    check_allocations()
