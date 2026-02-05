from django.core.management.base import BaseCommand

from coldfront.core.allocation.models import (
    Allocation,
    AllocationStatusChoice,
    AllocationLinkage,
)
from coldfront.core.allocation.signals import allocation_activate


class Command(BaseCommand):
    help = "Activate specified storage allocations in 'New' status"

    def add_arguments(self, parser):
        parser.add_argument(
            "--allocations",
            nargs="+",
            type=int,
            required=True,
            help="List of storage allocation IDs to activate",
        )

    def handle(self, *args, **options):
        failed_allocations = []

        allocations_ids = options["allocations"]

        parent_allocations = []
        sub_allocations = []

        for allocation_id in allocations_ids:
            allocation_linkage = AllocationLinkage.objects.filter(
                children__pk=allocation_id
            )

            if allocation_linkage.count() > 0:
                sub_allocations.append(allocation_id)
            else:
                parent_allocations.append(allocation_id)

        for allocations in [parent_allocations, sub_allocations]:
            for allocation_id in allocations:
                try:
                    self._activate_allocation(allocation_id)
                except ValueError as e:
                    failed_allocations.append(
                        {"allocation_id": allocation_id, "error": str(e)}
                    )

        if failed_allocations:
            print("Some allocations failed to activate:")
            for failure in failed_allocations:
                print(
                    f" - Allocation ID {failure['allocation_id']}: {failure['error']}"
                )

    def _activate_allocation(self, allocation_id):
        print(f"Activating storage allocation with ID: {allocation_id}")

        try:
            allocation = Allocation.objects.get(pk=allocation_id)
        except Allocation.DoesNotExist:
            print(f"Allocation with ID {allocation_id} does not exist.")
            raise ValueError(f"Allocation with ID {allocation_id} does not exist.")

        if allocation.status.name != "New":
            raise ValueError(
                f"Allocation with ID {allocation_id} is not in 'New' status."
            )

        allocation.status = AllocationStatusChoice.objects.get(name="Active")
        allocation.save()

        allocation_activate.send(sender=self.__class__, allocation_pk=allocation.pk)
