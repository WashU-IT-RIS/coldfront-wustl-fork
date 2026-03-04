from django.core.management.base import BaseCommand

from coldfront.core.allocation.models import Allocation, AllocationAttribute
from icecream import ic


class Command(BaseCommand):
    def add_arguments(self, parser) -> None:

        parser.add_argument(
            "--export-path",
            nargs="?",
            type=str,
            help=f'The export path to clean up (Defaults to "")',
            default="",
        )

        parser.add_argument(
            "--allocation-ids",
            nargs="+",
            type=int,
            required=True,
            help="List of storage allocation IDs to consider for export path cleanup separated by space (e.g. --allocation-ids 1 2 3) or by comma (e.g. --allocation-ids 1,2,3)",
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Returns the affected export paths without changing them",
        )

    def handle(self, *args, **options) -> None:
        allocation_ids = options["allocation_ids"]
        export_path = options["export_path"]
        dry_run = options["dry_run"]
        clean_export_path(export_path, allocation_ids, dry_run)


def clean_export_path(
    export_path: str, allocation_ids: list[int], dry_run: bool
) -> None:
    ic(allocation_ids)
    ic(export_path)
    ic(dry_run)

    allocation_attributes_to_be_cleaned = AllocationAttribute.objects.filter(
        allocation_id__in=allocation_ids,
        allocation__status__name__in=[ "New", "Active", "Pending"],
        allocation_attribute_type__name="storage_export_path",
    )

    before_values = allocation_attributes_to_be_cleaned.values_list(
        "allocation_id", "value"
    )
    if dry_run:
        ic("Dry run enabled. The following storage_export_path would be cleaned:")
        for allocation_id, current_export_path in before_values:
            ic(f" - Allocation ID {allocation_id}: {current_export_path}")
        return None

    allocation_attributes_to_be_cleaned.update(value=export_path)

    ic("Storage export paths have been cleaned for the following allocations:")
    for allocation_id, _ in allocation_attributes_to_be_cleaned.values_list(
        "allocation_id", "value"
    ):
        ic(f' - Allocation ID {allocation_id}: "{export_path}"')
