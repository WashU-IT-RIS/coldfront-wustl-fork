from coldfront.core.allocation.models import Allocation, Resource, AllocationAttribute
from django.db.models import OuterRef, Subquery

def change_subscription_to_consumption():
    storage_resources = Resource.objects.filter(resource_type__name="Storage")
    allocations = Allocation.objects.filter(status__name="Active", resources__in=storage_resources)

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
                allocation_attribute_type__name="service_rate_category",
            ).update(value="consumption") 