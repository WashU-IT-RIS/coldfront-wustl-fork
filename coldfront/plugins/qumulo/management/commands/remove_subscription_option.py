from django.core.management.base import BaseCommand
from coldfront.core.allocation.models import Allocation, Resource, AllocationAttribute, AllocationAttributeType
from django.db.models import OuterRef, Subquery
from coldfront.core.resource.models import ResourceType

class Command(BaseCommand):

    def handle(self, *args, **options):
        print("Changing all Subscription Service Rate Categories to Consumption")

        storage_resources = Resource.objects.filter(resource_type__name="Storage")
        allocations = list(
            Allocation.objects.filter(
                resources__in=[storage_resources], status__name="Active" 
            )
        )

        service_rate_category_sub_query = AllocationAttribute.objects.filter(
            allocation=OuterRef("pk"),
            allocation_attribute_type__name="service_rate_category",
        ).values("value")[:1]
        allocations = allocations.annotate(
            service_rate_category=Subquery(service_rate_category_sub_query)
        )

        for allocation in allocations:
            if allocation.service_rate_category == "subscription":
               AllocationAttribute.objects.filter(
                    allocation=allocation,
                    allocation_attribute_type__name="billing_cycle",
                ).update(value="consumption") 