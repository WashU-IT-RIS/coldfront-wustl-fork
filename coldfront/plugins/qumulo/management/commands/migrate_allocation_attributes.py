from coldfront.core.allocation.models import AllocationAttributeType, Allocation, AllocationAttribute
from coldfront.core.resource.models import Resource
from django.core.management.base import BaseCommand

from django.db.models import OuterRef, Subquery


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("Updating Qumulo Allocation Attributes")
        # updating required allocation attributes for all projects
        # need to add something to keep `secure` from being changed later
        # since Coldfront UI allows direct editing
        self._migrate_allocation_attribute("secure", "No")
        self._migrate_allocation_attribute("audit", "No")

    def _migrate_allocation_attribute(self, attribute_name, default_value):
        attribute_type = AllocationAttributeType.objects.get(name=attribute_name)
        attribute_sub_q = AllocationAttribute.objects.filter(
            allocation=OuterRef("pk"),
            allocation_attribute_type=attribute_type
        ).values("value")[:1]

        resource = Resource.objects.get(name="Storage2")
        all_storage_2_allocations = Allocation.objects.filter(resources=resource)
        all_storage_2_allocations = all_storage_2_allocations.annotate(
            secure=Subquery(attribute_sub_q)
        )

        for allocation in all_storage_2_allocations:
            if getattr(allocation, attribute_name, None) is None:
                AllocationAttribute.objects.create(
                    allocation_attribute_type=attribute_type,
                    allocation=allocation,
                    value=default_value
                )
