from django_q.tasks import async_task

from coldfront.plugins.qumulo.services.allocation_service import AllocationService
from coldfront.core.allocation.models import Allocation

import json


class BulkSubAllocationUpdateView(LoginRequiredMixin, TemplateView):
    template_name = "bulk_suballocation_update.html"

    def post(self, request: HttpRequest, *args, **kwargs):

        body = json.loads(request.body.decode("utf-8"))
        ro_users = body["roUsers"]
        rw_users = body["rwUsers"]
        allocation_ids = body["allocationIds"]

        allocations = Allocation.objects.filter(id__in=allocation_ids)

        for allocation in allocations:
            if len(ro_users) > 0:
                async_task(
                    AllocationService.add_access_users,
                    "ro",
                    ro_users,
                    allocation,
                    self.request.user.id,
                )
            if len(rw_users) > 0:
                async_task(
                    AllocationService.add_access_users,
                    "rw",
                    rw_users,
                    allocation,
                    self.request.user.id,
                )

        return HttpResponse()