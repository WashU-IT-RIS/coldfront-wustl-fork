from icecream import ic

from django.core.management.base import BaseCommand

from coldfront.plugins.qumulo.services.itsm.migrate_to_coldfront import (
    MigrateToColdfront,
)

from icecream import ic


class Command(BaseCommand):

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "fileset", type=str, help="The fileset_name or fileset_alias"
        )
        parser.add_argument(
            "--fileset_alias",
            action="store_true",
            help="Queries by fileset_alias instead of by fileset_name",
        )
        parser.add_argument(
            "--name",
            action="store_true",
            help="Queries by name instead of by fileset_name",
        )

    def handle(self, *args, **options) -> None:
        fileset = options["fileset"]
        ic(fileset)
        find_by_alias = options["fileset_alias"]
        ic(find_by_alias)
        find_by_name = options["name"]
        ic(find_by_name)

        migrate_from_itsm_to_coldfront = MigrateToColdfront()
        if find_by_alias:
            result = migrate_from_itsm_to_coldfront.by_fileset_alias(fileset)
        elif find_by_name:
            result = migrate_from_itsm_to_coldfront.by_fileset_storage_name(fileset)
        else:
            result = migrate_from_itsm_to_coldfront.by_fileset_name(fileset)

        ic(result)
