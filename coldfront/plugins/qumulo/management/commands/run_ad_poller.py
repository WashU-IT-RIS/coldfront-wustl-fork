from django.core.management.base import BaseCommand

from django_q.tasks import async_chain

from coldfront.plugins.qumulo.tasks import (
    poll_ad_groups,
    conditionally_update_storage_allocation_statuses,
)
from coldfront.plugins.qumulo.management.commands.check_billing_cycles import (
    check_allocations,
)


class Command(BaseCommand):
    help = (
        "Run Active Directory poller to update ACL allocations and storage allocations"
    )

    def handle(self, *args, **options):
        print("Running AD Poller")
        async_chain(
            [
                (poll_ad_groups),
                (conditionally_update_storage_allocation_statuses),
                (check_allocations),
            ]
        )
