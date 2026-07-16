from datetime import date, datetime, timedelta

from django.http import (
    JsonResponse,
    HttpRequest,
    HttpResponseBadRequest,
    HttpResponseNotFound,
)
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from coldfront.core.allocation.models import Allocation, AllocationAttributeUsage
from coldfront.core.user.models import User


class UsageAllocations(View):
    def get(self, request: HttpRequest, *args, **kwargs):
        allocations = Allocation.objects.filter(
            resources__resource_type__name="Storage"
        )
        allocation_path_map = map(
            lambda allocation: allocation.get_attribute("storage_filesystem_path"),
            allocations,
        )

        return JsonResponse({"allocations": list(allocation_path_map)})
