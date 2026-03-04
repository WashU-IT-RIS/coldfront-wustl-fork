from django.core.management.base import BaseCommand

from coldfront.core.allocation.models import Allocation, AllocationAttribute
from icecream import ic


class Command(BaseCommand):
    def add_arguments(self, parser) -> None:

        parser.add_argument(
            "--billing-cycle",
            nargs="?",
            type=str,
            help=f'The billing cycle to clean up (Defaults to "monthly")',
            default="monthly",
        )

        parser.add_argument(
            "--allocation-ids",
            nargs="+",
            type=int,
            required=True,
            help="List of storage allocation IDs to consider for billing cycle cleanup separated by space (e.g. --allocation-ids 1 2 3) or by comma (e.g. --allocation-ids 1,2,3)",
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Returns the affected billing cycles without changing them",
        )

    def handle(self, *args, **options) -> None:
        allocation_ids = options["allocation_ids"]
        billing_cycle = options["billing_cycle"]
        dry_run = options["dry_run"]
        clean_billing_cycle(billing_cycle, allocation_ids, dry_run)


def clean_billing_cycle(
    billing_cycle: str, allocation_ids: list[int], dry_run: bool
) -> None:
    ic(allocation_ids)
    ic(billing_cycle)
    ic(dry_run)

    allocation_to_be_cleaned = Allocation.objects.filter(
        id__in=allocation_ids, status__name__in=["New", "Active", "Pending"]
    ).exclude(allocationattribute__allocation_attribute_type__name="billing_cycle")

    before_values = allocation_to_be_cleaned.values_list("id", "status__name")
    if dry_run:
        ic("Dry run enabled. The following billing cycles would be created:")
        for allocation_id, status in before_values:
            ic(f" - Allocation ID {allocation_id}: {status}")
        return None

    for allocation in allocation_to_be_cleaned:
        AllocationAttribute.objects.get_or_create(
            allocation=allocation,
            allocation_attribute_type_name="billing_cycle",
            defaults={"value": billing_cycle},
        )

    ic("Billing cycles have been cleaned for the following allocations:")
    for allocation_id in allocation_to_be_cleaned.values_list("id"):
        ic(f' - Allocation ID {allocation_id}: "{billing_cycle}"')
