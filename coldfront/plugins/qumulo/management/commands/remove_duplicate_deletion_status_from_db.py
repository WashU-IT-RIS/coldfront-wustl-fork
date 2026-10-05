from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from coldfront.core.allocation.models import Allocation, AllocationStatusChoice


class Command(BaseCommand):
    help = "Removes unused 'Ready for Deletion' status choices without changing allocations or 'Ready for deletion' choices."

    def handle(self, *args, **options):
        status_choices = AllocationStatusChoice.objects.select_for_update().filter(
            name="Ready for Deletion"
        )
        legacy_status_ids = [
            status.pk
            for status in status_choices
            if status.name == "Ready for Deletion"
        ]

        if Allocation.objects.filter(status_id__in=legacy_status_ids).exists():
            raise CommandError(
                "Allocations still reference 'Ready for Deletion'. "
                "Run consolidate_deletion_statuses first. "
                "No status choices were deleted."
            )

        AllocationStatusChoice.objects.filter(pk__in=legacy_status_ids).delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"Removed {len(legacy_status_ids)} 'Ready for Deletion' status choice(s)."
            )
        )
