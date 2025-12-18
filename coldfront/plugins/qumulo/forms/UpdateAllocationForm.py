from typing import Any
from coldfront.core.allocation.models import Allocation, AllocationAttribute
from coldfront.plugins.qumulo.forms.AllocationForm import AllocationForm
from django import forms
from coldfront.plugins.qumulo.validators import (
    validate_condo_project_quota,
    validate_filesystem_path_unique,
    validate_parent_directory,
)

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
        cleaned_data = super(forms.Form, self).clean()
        protocols = cleaned_data.get("protocols")
        storage_export_path = cleaned_data.get("storage_export_path")
        storage_ticket = self._upper(cleaned_data.get("storage_ticket", None))
        storage_quota = cleaned_data.get("storage_quota", 0)
        service_rate_categories = cleaned_data.get("service_rate_category", "")
        project_pk = cleaned_data.get("project_pk")
        current_quota = self.get_current_quota(self.allocation_id)

        if ("condo" in service_rate_categories) and (storage_quota != current_quota):
            validate_condo_project_quota(project_pk, storage_quota, current_quota)

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

        if self.fields["storage_filesystem_path"].disabled is False:
            storage_type = cleaned_data.get("storage_type")
            storage_filesystem_path = cleaned_data.get("storage_filesystem_path")
            try:
                validate_filesystem_path_unique(storage_filesystem_path, storage_type)
                validate_parent_directory(storage_filesystem_path, storage_type)
            except forms.ValidationError as error:
                self.add_error("storage_filesystem_path", error.message)
        
        return cleaned_data
    
    def get_current_quota(self, current_allocation: int) -> int:
        allocation_obj = Allocation.objects.get(pk=current_allocation)
        current_quota = AllocationAttribute.objects.filter(
        allocation=allocation_obj,
        allocation_attribute_type__name="storage_quota",
        ).values("value")[:1]
        current_quota = int(current_quota[0]['value'])
        
        return current_quota