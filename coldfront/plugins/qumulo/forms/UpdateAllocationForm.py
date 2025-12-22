import re

from typing import Any
from django import forms


from coldfront.core.project.models import Project
from coldfront.core.resource.models import Resource
from coldfront.core.user.models import User
from coldfront.core.allocation.models import AllocationAttribute, Allocation
from coldfront.plugins.qumulo.validators import (
    validate_uniqueness_storage_name_for_storage_type,
    validate_filesystem_path_unique,
    validate_parent_directory,
)
from coldfront.core.allocation.forms import AllocationForm

class UpdateAllocationForm(AllocationForm):
    def __init__(self, *args, **kwargs):
        self.allocation_id = kwargs.pop("allocation_id")
        super().__init__(*args, **kwargs)
        self.fields["storage_type"].disabled = True

        self.fields["storage_name"].disabled = True
        self.fields["storage_filesystem_path"].disabled = True

        self.fields["storage_filesystem_path"].validators = []
        self.fields["storage_name"].validators = []

        self.fields["prepaid_expiration"] = forms.DateTimeField(
            help_text="Allocation is paid until this date",
            label="Prepaid Expiration Date",
            required=False,
        )
        self.fields["prepaid_expiration"].disabled = True
        self.fields["rw_users"].required = (
            self.allocation_status_name != "READY FOR DELETION"
        )

    def clean(self) -> dict[str, Any]:
        # Always call the parent's clean method to ensure basic validation is performed
        cleaned_data = super(forms.Form, self).clean()
        protocols = cleaned_data.get("protocols")
        storage_export_path = cleaned_data.get("storage_export_path")
        storage_ticket = self._upper(cleaned_data.get("storage_ticket", None))
        requested_quota = cleaned_data.get("storage_quota", 0)

        if self.allocation_id is not None:
            current_quota = self.get_current_quota(self.allocation_id)
        
        if cleaned_data.get("storage_type") == "Storage2" and requested_quota > current_quota:
            diff = requested_quota - current_quota
            if diff >= 10:
                self.add_error(
                    "storage_quota",
                    "Increases of 10TB or more for Storage2 allocations require approval. Please contact support.",
                )
        

        if "nfs" in protocols:
            if storage_export_path == "":
                self.add_error(
                    "storage_export_path",
                    "Export Path must be defined when using NFS protocol",
                )

        if storage_ticket is not None:
            if "ITSD-" not in storage_ticket and len(storage_ticket) > 0:
                self.cleaned_data["storage_ticket"] = "ITSD-{:s}".format(storage_ticket)
            else:
                self.cleaned_data["storage_ticket"] = storage_ticket

        self.validate_unique_storage_name(cleaned_data=cleaned_data)

        if self.fields["storage_filesystem_path"].disabled is False:
            storage_filesystem_path = cleaned_data.get("storage_filesystem_path")
            try:
                storage_type = cleaned_data.get("storage_type", "")
                validate_filesystem_path_unique(storage_filesystem_path, storage_type)
                validate_parent_directory(storage_filesystem_path, storage_type)
            except forms.ValidationError as error:
                self.add_error("storage_filesystem_path", error.message)
    
    def get_current_quota(self, current_allocation: int) -> int:
        allocation_obj = Allocation.objects.get(pk=current_allocation)
        current_quota = AllocationAttribute.objects.filter(
        allocation=allocation_obj,
        allocation_attribute_type__name="storage_quota",
        ).values("value")[:1]
        current_quota = int(current_quota[0]['value'])

        return current_quota

