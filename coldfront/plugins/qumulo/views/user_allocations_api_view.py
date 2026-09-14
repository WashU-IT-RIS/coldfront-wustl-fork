from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View

from coldfront.core.allocation.models import Allocation, AllocationUser, User
from coldfront.plugins.qumulo.utils.acl_allocations import AclAllocations
from coldfront.plugins.qumulo.utils.oauth2 import SessionOrOAuth2RequiredMixin


class UserAllocationsApiView(SessionOrOAuth2RequiredMixin, View):
    http_method_names = ["get"]
    required_scopes = ["read"]

    @staticmethod
    def _get_storage_allocations(user) -> list:
        storage_allocation_pks = set()

        for allocation in Allocation.objects.filter(allocationuser__user=user):
            storage_allocation_pk = allocation.get_attribute("storage_allocation_pk")
            if storage_allocation_pk:
                storage_allocation_pks.add(int(storage_allocation_pk))

        return list(
            Allocation.objects.filter(pk__in=storage_allocation_pks)
        )

    def get(self, request, username: str, *args, **kwargs):
        user = get_object_or_404(User, username=username)

        allocations = []

        for storage_allocation in self._get_storage_allocations(user):
            access = []

            for access_key in ["rw", "ro"]:
                access_allocation = AclAllocations.get_access_allocation(
                    storage_allocation, access_key
                )
                if access_allocation and AllocationUser.objects.filter(
                    allocation=access_allocation, user=user
                ).exists():
                    access.append(access_key)

            if not access:
                continue

            allocations.append(
                {
                    "allocation_id": storage_allocation.pk,
                    "project_id": storage_allocation.project.pk,
                    "project_name": storage_allocation.project.title,
                    "storage_name": storage_allocation.get_attribute("storage_name"),
                    "storage_filesystem_path": storage_allocation.get_attribute(
                        "storage_filesystem_path"
                    ),
                    "status": storage_allocation.status.name,
                    "access": sorted(access),
                }
            )

        allocations.sort(key=lambda allocation: allocation["allocation_id"])

        return JsonResponse(
            {
                "username": user.username,
                "allocations": allocations,
            },
            status=200,
        )
