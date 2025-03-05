from django.http import JsonResponse, HttpRequest
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms.models import model_to_dict

from coldfront.core.allocation.models import Allocation, AllocationAttribute

import pprint


class Allocations(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, *args, **kwargs):
        page = request.GET.get("page", 1)
        limit = request.GET.get("limit", 100)
        start_index = (page - 1) * limit
        stop_index = start_index + limit

        sort = request.GET.get("sort", "id")

        allocations = list(
            Allocation.objects.filter(resources__name="Storage2").order_by(sort)[
                start_index:stop_index
            ]
        )

        allocations_dicts = list(
            map(
                self._sanitize_allocation,
                allocations,
            )
        )

        # pprint.pprint(allocations_dicts)
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
