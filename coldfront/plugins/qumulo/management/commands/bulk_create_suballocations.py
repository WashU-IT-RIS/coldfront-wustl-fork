import runpy

from django.core.management.base import BaseCommand
import json

from coldfront.plugins.qumulo.services.itsm.migrate_to_coldfront import (
    MigrateToColdfront,
)


class Command(BaseCommand):
    help = "Run the batch Qumulo suballocation creation script."

    def add_arguments(self, parser):
        parser.add_argument(
            "--fileset",
            dest="fileset",
            type=str,
            required=True,
            help="The fileset name to create allocations for.",
        )
        parser.add_argument(
            "--resource",
            dest="resource",
            type=str,
            required=True,
            help="The resource name to create allocations for. Currently this could be Storage2 or Storage3.",
        )
        parser.add_argument(
            "--allocation-attributes",
            dest="allocation_attributes",
            type=str,
            required=True,
            help="Path to a JSON file containing a list of allocation attribute objects.",
        )

    def handle(self, *args, **options):
        fileset = options.get("fileset")
        resource = options.get("resource")
        allocation_attributes_json = options.get("allocation_attributes")
        with open(allocation_attributes_json, encoding="utf-8") as allocation_file:
            allocation_attributes_class_ris = json.load(allocation_file)

        migrator = MigrateToColdfront()
        migrator.batch_create_allocations_and_sub_allocations(
            fileset, resource, allocation_attributes_class_ris
        )