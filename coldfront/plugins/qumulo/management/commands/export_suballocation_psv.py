from django.core.management.base import BaseCommand

from coldfront.core.allocation.models import (
    Allocation,
    AllocationStatusChoice,
    AllocationLinkage,
)
from coldfront.core.allocation.signals import allocation_activate


class Command(BaseCommand):
    help = "Assemble a psv of specified allocations and suballocations.  Intended to be used with the ACL parrallel reset script"

    def add_arguments(self, parser):
        parser.add_argument(
            "--allocations",
            nargs="+",
            type=str,
            required=True,
            help="List parent allocation paths to use.  ",
        )

    def handle(self, *args, **options):
        output_lines=[]
        allocation_paths = options["allocations"]
        
        for allocation_path in allocation_paths:
          output_lines = allocation_path + "|{}"
        
        self.stdout.write(output_lines)