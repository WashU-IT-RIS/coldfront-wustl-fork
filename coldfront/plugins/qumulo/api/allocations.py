from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms.models import model_to_dict

from coldfront.core.allocation.models import Allocation, AllocationAttribute


class Allocations(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        allocations = list(Allocation.objects.filter(resources__name="Storage2"))

        allocations_dicts = list(
            map(
                self._sanitize_allocation,
                allocations,
            )
        )

        return JsonResponse(allocations_dicts, safe=False)

    def _sanitize_allocation(self, allocation: Allocation):
        allocation_dict = model_to_dict(allocation)

        allocation_dict["resources"] = list(
            map(lambda resource: resource.name, allocation_dict["resources"])
        )

        allocation_dict["status"] = allocation.status.name

        allocation_attributes = list(
            AllocationAttribute.objects.filter(allocation=allocation)
        )
        allocation_dict["attributes"] = dict()

        for attribute in allocation_attributes:
            allocation_dict["attributes"][
                attribute.allocation_attribute_type.name
            ] = attribute.value

        return allocation_dict
