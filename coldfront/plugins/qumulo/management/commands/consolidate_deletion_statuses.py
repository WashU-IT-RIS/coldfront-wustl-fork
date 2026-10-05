from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from coldfront.core.allocation.models import Allocation, AllocationStatusChoice


class Command(BaseCommand):
    help = "Moves allocations from 'Ready for Deletion' to 'Ready for deletion' without removing either status choice."

    def handle(self, *args, **options):
        
        allocations = Allocation.objects.filter(
            status__name="Ready for Deletion"
        )
        updated_count = 0

        if allocations.exists():
            correct_status = AllocationStatusChoice.objects.filter(
                name="Ready for deletion"
            ).order_by("pk").first()
            if correct_status is None:
                raise CommandError(
                    "Status choice 'Ready for deletion' does not exist. "
                    "No allocations were updated."
                )
            updated_count = allocations.update(status=correct_status)

        self.stdout.write(
            self.style.SUCCESS(
                f"Updated {updated_count} allocation(s) from 'Ready for Deletion' to 'Ready for deletion'."
            )
    )
