from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import HttpResponse, HttpRequest

from django_q.tasks import async_task

from coldfront.plugins.qumulo.services.allocation_service import AllocationService
from coldfront.core.allocation.models import Allocation

import json


class UserAccessManagementView(LoginRequiredMixin, TemplateView):
    template_name = "user_management.html"

    def post(self, request: HttpRequest, *args, **kwargs):

        body = json.loads(request.body.decode("utf-8"))
        ro_users = body["roUsers"].sort()
        #ro_users.sort()
        rw_users = body["rwUsers"].sort()
        #rw_users.sort()
        allocation_ids = body["allocationIds"]

        allocations = Allocation.objects.filter(id__in=allocation_ids)

        for allocation in allocations:
            if len(ro_users) > 0:
                async_task(
                    AllocationService.add_access_users,
                    "ro",
                    ro_users,
                    allocation,
                )
            if len(rw_users) > 0:
                async_task(
                    AllocationService.add_access_users,
                    "rw",
                    rw_users,
                    allocation,
                )

        return HttpResponse()
