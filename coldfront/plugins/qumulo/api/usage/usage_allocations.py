from django.http import (
    JsonResponse,
    HttpRequest,
)
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from coldfront.core.allocation.models import (
    Allocation,
)


class UsageAllocations(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, *args, **kwargs):
        allocations = Allocation.objects.filter(
            resources__resource_type__name="Storage", status__name="Active"
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
                "id": allocation.pk,
                "path": allocation.get_attribute("storage_filesystem_path"),
            },
            allocations,
        )

        return JsonResponse({"allocations": list(allocation_path_map)})
