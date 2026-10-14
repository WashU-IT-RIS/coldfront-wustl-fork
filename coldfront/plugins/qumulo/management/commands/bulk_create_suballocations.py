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
            "--allocation-attributes",
            dest="allocation_attributes",
            type=str,
            required=True,
            help="Path to a JSON file containing a list of allocation attribute objects.",
        )

    def handle(self, *args, **options):
        allocation_attributes_json = options.get("allocation_attributes")
        with open(allocation_attributes_json, encoding="utf-8") as allocation_file:
            allocation_attributes_class_ris = json.load(allocation_file)

        # if not isinstance(allocation_attributes_class_ris, list) or not all(
        # isinstance(attributes, dict) for attributes in allocation_attributes_class_ris
        # ):
        #     raise ValueError("Allocation attributes JSON must contain a list of objects.")


        migrator = MigrateToColdfront()
        migrator.batch_create_allocations_and_sub_allocations("di2-cap", "Storage3", allocation_attributes_class_ris)