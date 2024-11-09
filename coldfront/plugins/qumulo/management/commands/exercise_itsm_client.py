from django.core.management.base import BaseCommand

from coldfront.plugins.qumulo.services.itsm.itsm_client import ItsmClient


class Command(BaseCommand):

    def handle(self, *args, **options):
        print("Manually exercising ITSM client")
        itsm_client = ItsmClient()
        import pdb
        pdb.set_trace()
        # itsm_client.get_fs1_allocation_by_fileset_name("jin810_active")
        # itsm_client.get_fs1_allocation_by_fileset_name("not_going_to_be_found")
        # itsm_client.get_fs1_allocation_by_fileset_name()
        # itsm_client.get_fs1_allocation_by_fileset_alias("halllab")
        # itsm_client.get_fs1_allocation_by_fileset_alias("not_going_to_be_found")
        # itsm_client.get_fs1_allocation_by_fileset_alias()