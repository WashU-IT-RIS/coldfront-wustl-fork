from coldfront.core.allocation.models import AllocationAttributeType, Allocation, AllocationAttribute
from coldfront.core.resource.models import Resource
from django.core.management.base import BaseCommand

from django.db.models import OuterRef, Subquery


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("Updating Qumulo Allocation Attributes")
        # updating required allocation attributes for all projects

        secure_type = AllocationAttributeType.objects.get(name="secure")
        secure_sub_q = AllocationAttribute.objects.filter(
            allocation=OuterRef("pk"),
            allocation_attribute_type=secure_type
        ).values("value")[:1]


        resource = Resource.objects.get(name="Storage2")
        all_storage_2_allocations = Allocation.objects.filter(resources=resource)
        all_storage_2_allocations = all_storage_2_allocations.annotate(
            secure=Subquery(secure_sub_q)
        )

        for allocation in all_storage_2_allocations:
            if allocation.secure is None:
                AllocationAttribute.objects.create(
                    allocation_attribute_type=secure_type,
                    allocation=allocation,
                    value="No"
                )
