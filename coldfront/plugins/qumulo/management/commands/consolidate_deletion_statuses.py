from django.core.management.base import BaseCommand
from django.db import transaction

from coldfront.core.allocation.models import Allocation, AllocationStatusChoice


class Command(BaseCommand):
    help = "Moves allocations from 'Ready for Deletion' to 'Ready for deletion' without removing either status choice."

    def handle(self, *args, **options):
        with transaction.atomic():
            legacy_status = AllocationStatusChoice.objects.filter(
                name="Ready for Deletion"
            ).first()
            updated_count = 0

            if legacy_status is not None:
                canonical_status, _ = AllocationStatusChoice.objects.get_or_create(
                    name="Ready for deletion"
                )
                updated_count = Allocation.objects.filter(
                    status=legacy_status
                ).update(status=canonical_status)

        self.stdout.write(
            self.style.SUCCESS(
                f"Updated {updated_count} allocation(s) from 'Ready for Deletion' to 'Ready for deletion'."
            )
        )
