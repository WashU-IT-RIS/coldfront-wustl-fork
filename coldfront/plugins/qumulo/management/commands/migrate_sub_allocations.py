from django.core.management.base import BaseCommand

from coldfront.plugins.qumulo.services.itsm.migrate_sub_allocations_implementation import (
    MigrateSubAllocationsImplementation
)


import json


class Command(BaseCommand):

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "sub_alloc_list", type=str, help="The JSON string containing sub-alloc info"
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Dry run the sub-alloc migration",
        )

    def handle(self, *args, **options) -> None:
        import pdb

        # pdb.set_trace()
        
        sub_alloc_list_str = options["sub_alloc_list"]
        dry_run = options["dry_run"]
        sub_alloc_list = json.loads(sub_alloc_list_str)

        migration_handler = MigrateSubAllocationsImplementation()

        # pdb.set_trace()

        for sub_alloc_group in sub_alloc_list:
            parent_allocation_id = sub_alloc_group["parent_allocation_id"]
            sub_allocs_to_create = sub_alloc_group["project_dir_info_list"]
            migration_handler.create_sub_allocations(parent_allocation_id, sub_allocs_to_create, dry_run)
