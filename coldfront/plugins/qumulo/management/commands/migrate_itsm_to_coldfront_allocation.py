from django.core.management.base import BaseCommand

from coldfront.plugins.qumulo.services.itsm.migrate_to_coldfront import MigrateToColdfront

from icecream import ic

class Command(BaseCommand):

    def handle(self, *args, **options):

        ic(args)
        ic(options)

        fileset_name = None
        fileset_alias = None
        for key, value in options.items():
            if key == "fileset_name":
                fileset_name = value
            if key == "fileset_alias":
                fileset_alias = value

        migrate_from_itsm_to_coldfront = MigrateToColdfront()
        result = None
        if fileset_name:
            result = migrate_from_itsm_to_coldfront.by_fileset_name(fileset_name)

        if fileset_alias:
            result = migrate_from_itsm_to_coldfront.by_fileset_alias(fileset_alias)

        ic(result)
