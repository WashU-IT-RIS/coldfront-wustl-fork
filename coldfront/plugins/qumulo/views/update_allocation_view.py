from django.contrib import messages
from django.urls import reverse_lazy
from django_q.tasks import async_task

from typing import Union, Optional
from datetime import datetime

import json
import logging

from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttribute,
    AllocationAttributeType,
    AllocationAttributeChangeRequest,
    AllocationChangeRequest,
    AllocationChangeStatusChoice,
    AllocationLinkage,
    AllocationUser,
)

from coldfront.core.user.models import User

from coldfront.plugins.qumulo.forms.UpdateAllocationForm import UpdateAllocationForm
from coldfront.plugins.qumulo.hooks import acl_reset_complete_hook
from coldfront.plugins.qumulo.tasks import addMembersToADGroup, reset_allocation_acls
from coldfront.plugins.qumulo.views.allocation_view import AllocationView
from coldfront.plugins.qumulo.utils.acl_allocations import AclAllocations
from coldfront.plugins.qumulo.utils.active_directory_api import ActiveDirectoryAPI


logger = logging.getLogger(__name__)


class UpdateAllocationView(AllocationView):
    form_class = UpdateAllocationForm
    template_name = "update_allocation.html"
    success_url = reverse_lazy("home")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "Update Allocation"
        context["allocation_has_children"] = self._allocation_linkage_exists()
        allocation_id = self.kwargs.get("allocation_id")
        allocation = Allocation.objects.get(pk=allocation_id)
        alloc_status = allocation.status.name

        if alloc_status == "Pending":
            pending_status = True
        else:
            pending_status = False
        context["is_pending"] = pending_status

        return context

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
            "billing_exempt",
            "department_number",
            "billing_cycle",
            "technical_contact",
            "billing_contact",
            "service_rate",
            "billing_cycle",
            "prepaid_time",
            "prepaid_billing_date",
            "prepaid_expiration",
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

    def form_valid(
        self, form: UpdateAllocationForm, parent_allocation: Optional[Allocation] = None
    ):
        if "reset_acls" in self.request.POST:
            self._reset_acls()
        else:
            self._updated_fields_handler(form, parent_allocation)
        return super(AllocationView, self).form_valid(form=form)

    def _acl_reset_message(self):
        name = Allocation.objects.get(
            pk=self.kwargs.get("allocation_id")
        ).get_attribute(name="storage_name")
        if self.request.POST.get("reset_sub_acls"):
            message = f"ACL reset initiated for {name} and its sub-allocations."
        else:
            message = f"ACL reset initiated for {name}."
        return message

    def _allocation_linkage_exists(self):
        has_linkage = True
        try:
            AllocationLinkage.objects.get(
                parent=Allocation.objects.get(pk=self.kwargs.get("allocation_id"))
            )
        except AllocationLinkage.DoesNotExist:
            has_linkage = False
        return has_linkage

    def _reset_acls(self):
        # bmulligan (20240903): "retry" and "timeout" are intended to be
        # arbitrarily high values.  It would be good if the application could
        # know or learn what they should be.  Testing has shown that the DEV
        # infrastructure can process a directory tree of about 90,500 items in
        # 62 minutes.
        task_id = async_task(
            reset_allocation_acls,
            User.objects.get(id=self.request.user.id).email,
            Allocation.objects.get(pk=self.kwargs.get("allocation_id")),
            True if self.request.POST.get("reset_sub_acls") == "on" else False,
            hook=acl_reset_complete_hook,
            q_options={"retry": 90000, "timeout": 86400},
        )
        messages.add_message(self.request, messages.SUCCESS, self._acl_reset_message())

    def _identify_new_form_values(
        self, allocation: Allocation, attributes_to_check, form_values
    ):
        attribute_changes = list(zip(attributes_to_check, form_values))
        new_values = []

        for change in attribute_changes:
            attribute, _ = AllocationAttribute.objects.get_or_create(
                allocation_attribute_type=AllocationAttributeType.objects.get(
                    name=change[0]
                ),
                allocation=allocation,
                defaults={"value": ""},
            )

            current_attribute = AllocationAttribute.objects.get(
                allocation_attribute_type__name=change[0], allocation=allocation
            )

            comparand = (
                int(current_attribute.value)
                if type(change[1]) is int
                else current_attribute.value
            )
            if comparand != change[1]:
                new_values.append((change[0], change[1]))

        return new_values

    def _updated_fields_handler(
        self, form: UpdateAllocationForm, parent_allocation: Optional[Allocation] = None
    ):
        form_data = form.cleaned_data

        allocation = Allocation.objects.get(pk=self.kwargs.get("allocation_id"))

        allocation_change_request = None

        # NOTE - "storage_protocols" will have special handling
        attributes_to_check = [
            "cost_center",
            "billing_exempt",
            "department_number",
            "billing_cycle",
            "technical_contact",
            "billing_contact",
            "service_rate",
            "storage_ticket",
            "storage_quota",
        ]

        form_values = [form_data.get(field_name) for field_name in attributes_to_check]

        # handle "storage_protocols" separately
        attributes_to_check.append("storage_protocols")
        form_values.append(json.dumps(form_data.get("protocols")))
        attribute_changes = self._identify_new_form_values(
            allocation, attributes_to_check, form_values
        )
        if len(attribute_changes):
            allocation_change_request = AllocationChangeRequest.objects.create(
                allocation=allocation,
                status=AllocationChangeStatusChoice.objects.get(name="Pending"),
                justification="updating",
                notes="updating",
                end_date_extension=10,
            )

            for change in attribute_changes:
                attribute = AllocationAttribute.objects.get(
                    allocation_attribute_type__name=change[0],
                    allocation=allocation,
                )
                AllocationAttributeChangeRequest.objects.create(
                    allocation_attribute=attribute,
                    allocation_change_request=allocation_change_request,
                    new_value=change[1],
                )

        # RW and RO users are not handled via an AllocationChangeRequest
        access_keys = ["rw", "ro"]
        for key in access_keys:
            access_users = form_data[key + "_users"]
            self.set_access_users(key, access_users, allocation)

        # needed for redirect logic to work
        self.success_id = str(allocation.id)

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

        users_to_add = list(set(access_users) - set(allocation_usernames))
        create_group_time = datetime.now()
        
        async_task(
            addMembersToADGroup, users_to_add, access_allocation, create_group_time
        )

        users_to_remove = set(allocation_usernames) - set(access_users)
        for allocation_username in users_to_remove:
            allocation_users.get(user__username=allocation_username).delete()
            active_directory_api.remove_member_from_group(
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
