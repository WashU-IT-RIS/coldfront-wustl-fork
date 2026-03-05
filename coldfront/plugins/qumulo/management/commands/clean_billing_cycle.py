from django.core.management.base import BaseCommand

from coldfront.core.allocation.models import Allocation, AllocationAttribute, AllocationAttributeType


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
            help="List of storage allocation IDs to consider for billing cycle cleanup separated by space (e.g. --allocation-ids 1 2 3)",
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
        self.clean_billing_cycle(billing_cycle, allocation_ids, dry_run)

    def clean_billing_cycle(
        self, billing_cycle: str, allocation_ids: list[int], dry_run: bool
    ) -> None:
        self.stdout.write(f"{allocation_ids=}")
        self.stdout.write(f"{billing_cycle=}")
        self.stdout.write(f"{dry_run=}")

        allocation_to_be_cleaned = Allocation.objects.filter(
            id__in=allocation_ids, status__name__in=["New", "Active", "Pending"]
        ).exclude(allocationattribute__allocation_attribute_type__name="billing_cycle")

        before_values = allocation_to_be_cleaned.values_list("id", "status__name")
        if dry_run:
            self.stdout.write(
                "Dry run enabled. Billing cycles would be created for the following allocations:"
            )
            for allocation_id, status in before_values:
                self.stdout.write(f" - Allocation ID {allocation_id}: {status}")
            return None

        billing_cycle_type = AllocationAttributeType.objects.get(name="billing_cycle")
        for allocation in allocation_to_be_cleaned:
            # The get_or_create is used here to ensure that if the billing_cycle attribute already exists for an allocation,
            # it won't be overwritten. This is a safety measure to prevent unintended data changes.
            AllocationAttribute.objects.get_or_create(
                allocation=allocation,
                allocation_attribute_type=billing_cycle_type,
                defaults={"value": billing_cycle},
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Billing cycles have been created for the following allocations: "
            )
        )
        cleaned_allocations = Allocation.objects.filter(
            id__in=allocation_ids,
            status__name__in=["New", "Active", "Pending"],
            allocationattribute__allocation_attribute_type=billing_cycle_type,
        ).values_list("id", "allocationattribute__value")

        for allocation_id, billing_cycle in cleaned_allocations:
            self.stdout.write(
                self.style.SUCCESS(
                    f' - Allocation ID: {allocation_id}, billing_cycle: "{billing_cycle}"'
                )
            )
