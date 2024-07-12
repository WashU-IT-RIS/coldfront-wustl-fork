from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy

import json

from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttribute,
    AllocationAttributeType,
    AllocationAttributeChangeRequest,
    AllocationChangeRequest,
    AllocationChangeStatusChoice,
    AllocationUser,
)
from coldfront_plugin_qumulo.forms import UpdateAllocationForm
from coldfront_plugin_qumulo.views.allocation_view import AllocationView
from coldfront_plugin_qumulo.utils.acl_allocations import AclAllocations
from coldfront_plugin_qumulo.utils.active_directory_api import ActiveDirectoryAPI


class UpdateAllocationView(AllocationView):
    form_class = UpdateAllocationForm
    template_name = "allocation.html"
    success_url = reverse_lazy("home")

    def get_form_kwargs(self):
        kwargs = super(UpdateAllocationView, self).get_form_kwargs()
        kwargs["user_id"] = self.request.user.id

        allocation_id = self.kwargs.get("allocation_id")
        allocation = Allocation.objects.get(pk=allocation_id)
        allocation_attrs = AllocationAttribute.objects.filter(allocation=allocation_id)

        form_data = {
            "project_pk": allocation.project.pk,
        }

        allocation_attribute_keys = [
            "storage_name",
            "storage_quota",
            "protocols",
            "storage_filesystem_path",
            "storage_export_path",
            "storage_ticket",
            "cost_center",
            "department_number",
            "technical_contact",
            "billing_contact",
            "service_rate",
        ]
        for key in allocation_attribute_keys:
            form_data[key] = self.get_allocation_attribute(
                allocation_attributes=allocation_attrs, attribute_key=key
            )

        access_keys = ["rw", "ro"]
        for key in access_keys:
            form_data[key + "_users"] = self.get_access_users(key, allocation)

        kwargs["initial"] = form_data
        return kwargs

    def form_valid(self, form: UpdateAllocationForm):
        form_data = form.cleaned_data

        allocation = Allocation.objects.get(pk=self.kwargs.get("allocation_id"))

        allocation_change_request = AllocationChangeRequest.objects.create(
            allocation=allocation,
            status=AllocationChangeStatusChoice.objects.get(name="Pending"),
            justification="updating",
            notes="updating",
            end_date_extension=10,
        )

        storage_quota_attribute = AllocationAttribute.objects.get(
            allocation_attribute_type=AllocationAttributeType.objects.get(
                name="storage_quota"
            )
        )

        if storage_quota_attribute.value != form_data.get("storage_quota"):
            AllocationAttributeChangeRequest.objects.create(
                allocation_attribute=storage_quota_attribute,
                allocation_change_request=allocation_change_request,
                new_value=form_data.get("storage_quota"),
            )

        storage_protocols = json.dumps(form_data.get("protocols"))

        storage_protocols_attribute = AllocationAttribute.objects.get(
            allocation_attribute_type=AllocationAttributeType.objects.get(
                name="storage_protocols"
            )
        )

        if storage_protocols_attribute.value != storage_protocols:
            AllocationAttributeChangeRequest.objects.create(
                allocation_attribute=storage_protocols_attribute,
                allocation_change_request=allocation_change_request,
                new_value=storage_protocols,
            )

        access_keys = ["rw", "ro"]
        for key in access_keys:
            access_users = form_data[key + "_users"]
            self.set_access_users(key, access_users, allocation)

        return super(AllocationView, self).form_valid(form)

    @staticmethod
    def set_access_users(
        access_key: str, access_users: list[str], storage_allocation: Allocation
    ):
        active_directory_api = ActiveDirectoryAPI()

        access_allocation = AclAllocations.get_access_allocation(
            storage_allocation, access_key
        )

        allocation_users = AllocationUser.objects.filter(allocation=access_allocation)
        allocation_usernames = [
            allocation_user.user.username for allocation_user in allocation_users
        ]

        for access_user in access_users:
            if access_user not in allocation_usernames:
                AclAllocations.add_user_to_access_allocation(
                    access_user, access_allocation
                )
                active_directory_api.add_user_to_ad_group(
                    access_user, access_allocation.get_attribute("storage_acl_name")
                )

        for allocation_username in allocation_usernames:
            if allocation_username not in access_users:
                allocation_users.get(user__username=allocation_username).delete()
                active_directory_api.remove_user_from_group(
                    allocation_username,
                    access_allocation.get_attribute("storage_acl_name"),
                )

    def get_allocation_attribute(self, allocation_attributes: list, attribute_key: str):
        for allocation_attribute in allocation_attributes:
            if (
                attribute_key == "protocols"
                and allocation_attribute.allocation_attribute_type.name
                == "storage_protocols"
            ):
                return json.loads(allocation_attribute.value)

            if allocation_attribute.allocation_attribute_type.name == attribute_key:
                return allocation_attribute.value

    @staticmethod
    def get_access_users(key: str, storage_allocation: Allocation) -> list[str]:
        access_allocation = AclAllocations.get_access_allocation(
            storage_allocation, key
        )

        access_allocation_users = AllocationUser.objects.filter(
            allocation=access_allocation
        )

        access_users = [
            allocation_user.user.username for allocation_user in access_allocation_users
        ]

        return access_users
