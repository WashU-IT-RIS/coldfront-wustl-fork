from django.core.management.base import BaseCommand

from coldfront.core.allocation.models import Allocation


class Command(BaseCommand):
    help = "Consolidates allocation deletion status labels by normalizing 'Ready for Deletion' to 'Ready for deletion'."

    def handle(self, *args, **options):
        allocations = Allocation.objects.filter(status__name="Ready for Deletion")
        updated_count = 0

        for allocation in allocations:
            allocation.status.name = "Ready for deletion"
            allocation.status.save()
            updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Updated {updated_count} allocation(s) from 'Ready for Deletion' to 'Ready for deletion'."
            )
        )
