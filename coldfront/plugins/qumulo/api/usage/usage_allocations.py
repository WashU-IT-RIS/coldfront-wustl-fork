from datetime import date, datetime, timedelta

from django.http import (
    JsonResponse,
    HttpRequest,
    HttpResponseBadRequest,
    HttpResponseNotFound,
)
from django.db.models import Q
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttributeUsage,
    AllocationAttribute,
)

from pprint import pprint


class UsageAllocations(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, *args, **kwargs):
        allocations = Allocation.objects.filter(
            resources__resource_type__name="Storage", status__name="Active"
        )
        if not request.user.is_superuser and not request.user.is_staff:
            pi_allocations = allocations.filter(project__pi=request.user)
            billing_attributes = AllocationAttribute.objects.filter(
                allocation__in=allocations,
                allocation_attribute_type__name="billing_contact",
                value=request.user.username,
            ).select_related("allocation")
            billing_allocation_pks = map(
                lambda attribute: attribute.allocation.pk, billing_attributes
            )
            billing_allocations = allocations.filter(pk__in=billing_allocation_pks)

            allocations = (pi_allocations | billing_allocations).distinct()

        allocation_path_map = map(
            lambda allocation: allocation.get_attribute("storage_filesystem_path"),
            allocations,
        )

        return JsonResponse({"allocations": list(allocation_path_map)})
