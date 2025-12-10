from typing import Any
from coldfront.core.allocation.models import Allocation, AllocationAttribute, AllocationStatusChoice
from coldfront.core.resource.models import Resource
from coldfront.plugins.qumulo.forms.AllocationForm import AllocationForm
from django import forms
from django.db.models import OuterRef, Subquery, Sum
from django.utils.translation import gettext_lazy

from coldfront.plugins.qumulo.validators import calculate_total_project_quotas


class UpdateAllocationForm(AllocationForm):
    def __init__(self, *args, **kwargs):
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
    
    def calculate_total_project_quotas(project_pk, storage_quota):
        print("this was called from the update form")
        storage_resources = Resource.objects.filter(resource_type__name="Storage")
        project_allocations = Allocation.objects.filter(
            project__id=project_pk,
            resources__in=storage_resources,
        )
        current_allocation = Allocation.objects.filter(name=UpdateAllocationForm.cleaned_data.get("storage_name")).first()
        current_quota = current_allocation.allocationattribute_set.get(allocation_attribute_type__name="storage_quota").value
        if storage_quota != current_quota:
            if storage_quota > current_quota:
                diff = storage_quota - current_quota
            else:
                diff = current_quota - storage_quota
        else:
            diff = 0
        storage_quota_sub_query = AllocationAttribute.objects.filter(
            allocation=OuterRef("pk"),
            allocation_attribute_type__name="storage_quota",
        ).values("value")[:1]
        project_allocations = project_allocations.annotate(
            storage_quota=Subquery(storage_quota_sub_query)
        )
        total_storage_quota = (
            project_allocations.aggregate(total=Sum("storage_quota"))["total"] or 0
        )
        total_storage_quota = total_storage_quota + diff
        return total_storage_quota

    def validate_condo_project_quota(project_pk, storage_quota):
        CONDO_PROJECT_QUOTA = 1000
        quota_total = UpdateAllocationForm.calculate_total_project_quotas(project_pk, storage_quota)
        print("this was called from the update form")
        #I need a way to check if this form is creating or updating because the calculation is different depending on the scenario
        if quota_total > CONDO_PROJECT_QUOTA:
            raise forms.ValidationError(
                gettext_lazy(
                    f"Project quota exceeds condo limit of {CONDO_PROJECT_QUOTA} TB."
                )
            )
        
    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        protocols = cleaned_data.get("protocols")
        storage_export_path = cleaned_data.get("storage_export_path")
        storage_ticket = self._upper(cleaned_data.get("storage_ticket", None))
        storage_quota = cleaned_data.get("storage_quota", 0)
        service_rate_categories = cleaned_data.get("service_rate_category", "")
        project_pk = cleaned_data.get("project_pk")

        if "condo" in service_rate_categories:
            UpdateAllocationForm.validate_condo_project_quota(project_pk, storage_quota)

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
                AllocationForm.validate_filesystem_path_unique(storage_filesystem_path, storage_type)
                AllocationForm.validate_parent_directory(storage_filesystem_path, storage_type)
            except forms.ValidationError as error:
                self.add_error("storage_filesystem_path", error.message)
