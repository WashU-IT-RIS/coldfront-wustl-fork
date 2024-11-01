from django.core.management.base import BaseCommand
from coldfront.core.allocation.models import Allocation, Resource


class Command(BaseCommand):

    def handle(self, *args, **options):
        print("Zeroing all quota usages")

        storage_resource = Resource.objects.get(name="Storage")
        allocations = list(
            Allocation.objects.filter(
                resource__contains=storage_resource, status__name="Active"
            )
        )

        for allocation in allocations:
            allocation.set_usage("storage_quota", 0)
            allocation.save()