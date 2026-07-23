from django.http import (
    JsonResponse,
    HttpRequest,
)
from django.db.models import Subquery, OuterRef
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

from coldfront.core.allocation.models import Allocation, AllocationAttribute


class UsageAllocations(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, *args, **kwargs):
        storage_filesystem_path_query = Subquery(
            AllocationAttribute.objects.filter(
                allocation=OuterRef("pk"),
                allocation_attribute_type__name="storage_filesystem_path",
            ).values("value")
        )
        
        allocations = (
            Allocation.objects.parents()
            .annotate(storage_filesystem_path=storage_filesystem_path_query)
            .filter(resources__resource_type__name="Storage", status__name="Active")
        )
        
        if not request.user.is_superuser and not request.user.is_staff:
            pi_allocations = allocations.filter(project__pi=request.user)
            billing_allocations = allocations.filter(
                allocationattribute__allocation_attribute_type__name="billing_contact",
                allocationattribute__value=request.user.username,
            )
            technical_allocations = allocations.filter(
                allocationattribute__allocation_attribute_type__name="technical_contact",
                allocationattribute__value=request.user.username,
            )

            allocations = (
                pi_allocations | billing_allocations | technical_allocations
            ).distinct()

        allocation_path_map = map(
            lambda allocation: {
                "id": allocation[0],
                "path": allocation[1],
            },
            allocations.values_list("pk", "storage_filesystem_path"),
        )

        return JsonResponse({"allocations": list(allocation_path_map)})
