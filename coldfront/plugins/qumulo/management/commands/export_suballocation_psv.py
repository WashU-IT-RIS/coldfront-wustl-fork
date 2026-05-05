from django.core.management.base import BaseCommand

from coldfront.core.allocation.models import (
    Allocation,
    AllocationLinkage,AllocationAttributeType
)

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
        
        storage_filesystem_path_attribute_type = AllocationAttributeType.objects.get(
            name="storage_filesystem_path"
        )
        
        for allocation_path in allocation_paths:
          suballocations = []
          allocation = Allocation.objects.get(allocationattribute__allocation_attribute_type=storage_filesystem_path_attribute_type, allocationattribute__value=allocation_path)
          
          path_prefix = f"{allocation.get_attribute('storage_filesystem_path')}/Active/"
          
          try:
            allocation_linkage_children = AllocationLinkage.objects.get(parent=allocation).children.all()
          except AllocationLinkage.DoesNotExist:
            allocation_linkage_children = []

          for child_allocation in allocation_linkage_children:
            filesystem_path: str = child_allocation.get_attribute("storage_filesystem_path")
            
            path_suffix = filesystem_path.removeprefix(path_prefix)
            suballocations.append(path_suffix)
          
          output_lines = allocation_path + "|{" + ",".join(suballocations) + "}"
        
        self.stdout.write(output_lines)