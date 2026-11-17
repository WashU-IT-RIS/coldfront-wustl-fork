from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View

from coldfront.core.allocation.models import Allocation, User
from coldfront.plugins.qumulo.utils.oauth2 import SessionOrOAuth2RequiredMixin


class UserAllocationsApi(SessionOrOAuth2RequiredMixin, View):
    http_method_names = ["get"]
    required_scopes = ["read"]

    def get(self, request, username: str, *args, **kwargs):
        user = get_object_or_404(User, username=username)

        return_allocations = []
        access_allocations = Allocation.objects.filter(
            resources__resource_type__name="ACL", allocationuser__user=user
        )
        storage_allocations = dict()

        for access_allocation in access_allocations:
            storage_allocation_pk = access_allocation.get_attribute(
                "storage_allocation_pk"
            )

            access_name = access_allocation.resources.first().name
            if storage_allocation_pk in storage_allocations:
                storage_allocations[storage_allocation_pk].get("access", []).append(
                    access_name
                )
            else:
                storage_allocations[storage_allocation_pk] = {"access": [access_name]}

        storage_allocations_objects = Allocation.objects.filter(
            pk__in=storage_allocations.keys()
        )

        for storage_allocation in storage_allocations_objects:
            return_allocations.append(
                {
                    "allocation_id": storage_allocation.pk,
                    "project_id": storage_allocation.project.pk,
                    "project_name": storage_allocation.project.title,
                    "storage_name": storage_allocation.get_attribute("storage_name"),
                    "storage_filesystem_path": storage_allocation.get_attribute(
                        "storage_filesystem_path"
                    ),
                    "status": storage_allocation.status.name,
                    "access": sorted(
                        storage_allocations[storage_allocation.pk].get("access")
                    ),
                }
            )

        return_allocations.sort(key=lambda allocation: allocation["allocation_id"])

        return JsonResponse(
            {
                "username": user.username,
                "allocations": return_allocations,
            },
            status=200,
        )
