from django.core.management.base import BaseCommand
from coldfront.core.allocation.models import Allocation, Resource
from coldfront.core.resource.models import ResourceType


class Command(BaseCommand):

    def handle(self, *args, **options):
        print("Zeroing all quota usages")

        storage_resource_type = ResourceType.objects.get(name="Storage")
        resource = Resource.objects.filter(resource_type=storage_resource_type)
        allocations = list(
            Allocation.objects.filter(resources__in=[resource], status__name="Active")
        )

        for allocation in allocations:
            allocation.set_usage("storage_quota", 0)
            allocation.save()
