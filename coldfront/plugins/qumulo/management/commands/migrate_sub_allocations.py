from icecream import ic

from django.core.management.base import BaseCommand

from coldfront.plugins.qumulo.services.itsm.migrate_to_coldfront import (
    MigrateToColdfront,
)

from icecream import ic

import json


class Command(BaseCommand):

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "sub_alloc_list", type=str, help="The JSON string containing sub-alloc info"
        )

        parser.add_argument(
            "--dry-run",
            type=bool,
            action="store_true",
            help="Run the migration in dry run mode without making any changes",
        )

    def handle(self, *args, **options) -> None:
        import pdb
        
        sub_alloc_list_str = options["sub_alloc_list"]
        dry_run = options["dry_run"]
        sub_alloc_list = json.loads(sub_alloc_list_str)

        migrate_from_itsm_to_coldfront = MigrateToColdfront()

        pdb.set_trace()

        for sub_alloc_group in sub_alloc_list:
            parent_allocation_id = sub_alloc_group["parent_allocation_id"]
            sub_allocs_to_create = sub_alloc_group["project_dir_info_list"]
            migrate_from_itsm_to_coldfront.create_sub_allocations(parent_allocation_id, sub_allocs_to_create, dry_run)
