from django.http import JsonResponse, HttpRequest, HttpResponseBadRequest
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms.models import model_to_dict
from django.db.models import OuterRef
from django.core.exceptions import FieldError

from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttribute,
)


class Allocations(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, *args, **kwargs):
        page = request.GET.get("page", 1)
        limit = request.GET.get("limit", 100)
        start_index = (page - 1) * limit
        stop_index = start_index + limit

        sort = request.GET.get("sort", "id")
        is_attribute_sort = sort == "attributes"

        allocations_queryset = Allocation.objects.filter(resources__name="Storage2")
        try:
            if is_attribute_sort:
                attribute_sort = request.GET.get("attribute_sort")

                if attribute_sort is None:
                    return HttpResponseBadRequest("Attribute sort key not provided")

                sort = "selected_attr"
                if attribute_sort["order"] == "desc":
                    sort = "-selcted_attr"

                allocation_attributes = AllocationAttribute.objects.filter(
                    allocation=OuterRef("id"),
                    allocation__resources__name="Storage2",
                    allocation_attribute_type__name=attribute_sort["key"],
                ).values("value")

                allocations_queryset = allocations_queryset.annotate(
                    selected_attr=allocation_attributes
                )

            allocations_queryset = allocations_queryset.filter(
                resources__name="Storage2"
            ).order_by(sort)[start_index:stop_index]

        except FieldError:
            return HttpResponseBadRequest("Invalid sort key")

        allocations_dicts = list(
            map(
                self._sanitize_allocation,
                allocations_queryset,
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
