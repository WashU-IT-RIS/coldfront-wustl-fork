import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from coldfront.core.allocation.models import Allocation, AllocationUser
from coldfront.plugins.qumulo.utils.acl_allocations import AclAllocations
from coldfront.plugins.qumulo.utils.active_directory_api import ActiveDirectoryAPI
from coldfront.plugins.qumulo.utils.attestation import (
    attestation_gate_enabled,
    find_completed_attestation,
    # pre_onboard_group_name,
    # record_pending_attestation_event,
)
from coldfront.plugins.qumulo.utils.oauth2 import SessionOrOAuth2RequiredMixin
from coldfront.plugins.qumulo.utils.workday_api import (
    # CURRENT_ATTESTATION_CYCLE_ID,
    WorkdayAPI,
)
from typing import Union, cast


# Mutates AD group membership; not an HTML form, so CSRF is exempted here
# and mutation is instead gated by session login or an OAuth2 access token
# scoped to "write" (see SessionOrOAuth2RequiredMixin).
@method_decorator(csrf_exempt, name="dispatch")
class AllocationUsersApi(SessionOrOAuth2RequiredMixin, View):
    http_method_names = ["post", "delete"]
    required_scopes = ["write"]

    @staticmethod
    def _normalize_usernames(users: list[str]) -> list[str]:
        if not isinstance(users, list):
            return None

        normalized_users: list[str] = []
        for user in users:
            if not isinstance(user, str):
                return None

            username = user.strip()
            if username:
                normalized_users.append(username)

        return normalized_users

    @staticmethod
    def _parse_users(body: bytes):
        try:
            payload = json.loads(body.decode("utf-8") or "{}")
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

        users = AllocationUsersApi._normalize_usernames(payload.get("users"))
        if not users:
            return None

        return users

    @classmethod
    def _parse_access_users(self, body: bytes) -> Union[dict[str, list], None]:
        try:
            payload = json.loads(body.decode("utf-8") or "{}")
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

        if not payload.get("rw_users", None) and not payload.get("ro_users", None):
            return None

        access_users = {"rw": [], "ro": []}
        for access_key in ["rw", "ro"]:
            raw_users = payload.get(f"{access_key}_users", [])
            normalized_users = self._normalize_usernames(raw_users)
            if normalized_users is None:
                return None

            access_users[access_key] = normalized_users

        return access_users

    def post(self, request, allocation_id: int, *args, **kwargs):
        access_users = self._parse_access_users(request.body)
        if access_users is None:
            return JsonResponse(
                {
                    "detail": (
                        "Request body must be valid JSON and include a non-empty "
                        "'rw_users' and/or 'ro_users' array of usernames."
                    )
                },
                status=400,
            )

        storage_allocation = get_object_or_404(Allocation, pk=allocation_id)
        active_directory_api = ActiveDirectoryAPI()

        # See utils/attestation.py: while disabled (the default), this is a
        # no-op and grants behave exactly as before. Fetched once per
        # request, not once per user, since it's the same Workday query
        # regardless of which user is being checked.
        gate_enabled = attestation_gate_enabled()
        completed_records = (
            WorkdayAPI().get_completed_attestations() if gate_enabled else []
        )

        added_users = {"rw": [], "ro": []}
        pending_users = {"rw": [], "ro": []}
        storage_acl_name = {"rw": None, "ro": None}

        for access_key in ["rw", "ro"]:
            access_allocation = AclAllocations.get_access_allocation(
                storage_allocation, access_key
            )
            if not access_allocation:
                continue

            access_storage_acl_name = access_allocation.get_attribute(
                "storage_acl_name"
            )
            storage_acl_name[access_key] = access_storage_acl_name

            requested_usernames = access_users[access_key]
            if not requested_usernames:
                continue

            existing_usernames = set(
                AllocationUser.objects.filter(
                    allocation=access_allocation,
                    user__username__in=requested_usernames,
                ).values_list("user__username", flat=True)
            )

            new_usernames = [
                username
                for username in requested_usernames
                if username not in existing_usernames
            ]

            if not new_usernames:
                continue

            for username in new_usernames:
                completed = (
                    find_completed_attestation(
                        username, active_directory_api, completed_records
                    )
                    if gate_enabled
                    else True
                )

                # if gate_enabled and completed is None:
                #     record_pending_attestation_event(
                #         access_allocation,
                #         username,
                #         access_key,
                #         CURRENT_ATTESTATION_CYCLE_ID,
                #     )
                #     pending_users[access_key].append(username)
                #     continue

                if completed:
                    AclAllocations.add_user_to_access_allocation(
                        username, access_allocation
                    )
                    added_users[access_key].append(username)

        return JsonResponse(
            {
                "allocation_id": storage_allocation.pk,
                "added_users": added_users,
                "pending_users": pending_users,
                "storage_acl_name": storage_acl_name,
            },
            status=200,
        )

    def delete(self, request, allocation_id: int, *args, **kwargs):
        users = self._parse_users(request.body)
        if users is None:
            return JsonResponse(
                {
                    "detail": (
                        "Request body must be valid JSON and include a non-empty "
                        "'users' array of usernames."
                    )
                },
                status=400,
            )

        storage_allocation = get_object_or_404(Allocation, pk=allocation_id)

        removed_users = {"rw": [], "ro": []}
        storage_acl_name = {"rw": None, "ro": None}

        for access_key in ["rw", "ro"]:
            access_allocation = AclAllocations.get_access_allocation(
                storage_allocation, access_key
            )
            if not access_allocation:
                continue

            access_storage_acl_name = cast(
                Union[str, None], access_allocation.get_attribute("storage_acl_name")
            )
            storage_acl_name[access_key] = access_storage_acl_name

            userQuery = AllocationUser.objects.filter(
                allocation=access_allocation,
                user__username__in=users,
            )

            existing_usernames: list[str] = list(
                userQuery.values_list("user__username", flat=True)
            )

            userQuery.delete()

            removed_users[access_key] = existing_usernames

        return JsonResponse(
            {
                "allocation_id": storage_allocation.pk,
                "removed_users": removed_users,
                "storage_acl_name": storage_acl_name,
            },
            status=200,
        )
