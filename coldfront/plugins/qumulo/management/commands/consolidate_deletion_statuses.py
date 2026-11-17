from django.core.management.base import BaseCommand, CommandError

from coldfront.core.allocation.models import Allocation, AllocationStatusChoice


class Command(BaseCommand):
    help = "Moves allocations from 'Ready for Deletion' to 'Ready for deletion' without removing either status choice."

    def handle(self, *args, **options):
        status_choices = list(
            AllocationStatusChoice.objects.filter(
                name__in=["Ready for Deletion", "Ready for deletion"]
            ).order_by("pk").values_list("pk", "name")
        )
        legacy_status_ids = [
            status_id
            for status_id, name in status_choices
            if name == "Ready for Deletion"
        ]
        allocations = Allocation.objects.filter(
            status_id__in=legacy_status_ids
        )
        updated_count = 0

        if allocations.exists():
            correct_status_id = next(
                (
                    status_id
                    for status_id, name in status_choices
                    if name == "Ready for deletion"
                ),
                None,
            )
            if correct_status_id is None:
                raise CommandError(
                    "Status choice 'Ready for deletion' does not exist. "
                    "No allocations were updated."
                )
            updated_count = allocations.update(status_id=correct_status_id)

        self.stdout.write(
            self.style.SUCCESS(
                f"Updated {updated_count} allocation(s) from 'Ready for Deletion' to 'Ready for deletion'."
            )
        )
