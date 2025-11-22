from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import ValidationError
from django.views.generic.edit import FormView
from django.urls import reverse
from django.db.models import OuterRef, Subquery, Sum

from typing import Optional

import os
import json

from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttribute,
    AllocationAttributeType,
)

from coldfront.core.resource.models import Resource
from coldfront.plugins.qumulo.forms.AllocationForm import AllocationForm
from coldfront.plugins.qumulo.services.file_system_service import FileSystemService
from coldfront.plugins.qumulo.validators import validate_filesystem_path_unique


from coldfront.plugins.qumulo.services.allocation_service import AllocationService

from pathlib import PurePath
from datetime import date
from django.utils.translation import gettext_lazy


class AllocationView(LoginRequiredMixin, FormView):
    form_class = AllocationForm
    template_name = "allocation.html"
    new_allocation = None
    success_id = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["file_system_stats_storage2"] = FileSystemService.get_file_system_stats(
            "Storage2"
        )
        context["file_system_stats_storage3"] = FileSystemService.get_file_system_stats(
            "Storage3"
        )
        return context

    def get_form_kwargs(self):
        kwargs = super(AllocationView, self).get_form_kwargs()
        kwargs["user_id"] = self.request.user.id
        return kwargs

    def set_billing_cycle(form_data):
        billing_cycle = form_data.get("billing_cycle")
        prepaid_billing_date = form_data.get("prepaid_billing_date")
        if billing_cycle == "prepaid" and prepaid_billing_date > date.today():
            form_data["billing_cycle"] = "monthly"

    def calculate_total_project_quotas(form_data):
        storage_resources = Resource.objects.filter(resource_type__name="Storage")
        allocation_project = form_data.get("project_pk")
        project_allocations = Allocation.objects.filter(
            project__id=allocation_project,
            resources__in=storage_resources,
        )
        storage_quota_sub_query = AllocationAttribute.objects.filter(
            allocation=OuterRef("pk"),
            allocation_attribute_type__name="storage_quota",
        ).values("value")[:1]
        project_allocations = project_allocations.annotate(
            storage_quota=Subquery(storage_quota_sub_query)
        )
        total_storage_quota = project_allocations.aggregate(total=Sum("storage_quota"))[
            "total"
        ]
        total_storage_quota = total_storage_quota + form_data.get("storage_quota")
        return total_storage_quota

    def form_valid(
        self, form: AllocationForm, parent_allocation: Optional[Allocation] = None
    ):
        form_data = form.cleaned_data
        user = self.request.user
        storage_type = form_data.get("storage_type")
        storage_filesystem_path = form_data.get("storage_filesystem_path")
        is_absolute_path = PurePath(storage_filesystem_path).is_absolute()
        if form_data.get("service_rate_category") == "condo":
            quota_total = AllocationView.calculate_total_project_quotas(form_data)
            if quota_total > 1000:
                raise ValidationError(
                    gettext_lazy("Project quota exceeds condo limit of 1000 GB.")
                )

        if is_absolute_path:
            absolute_path = storage_filesystem_path
        else:
            # also need to retrieve the parent path if provided
            if parent_allocation:
                # should already contain storage_root path
                root_val = parent_allocation.get_attribute(
                    name="storage_filesystem_path"
                ).strip("/")
                prepend_val = f"{root_val}/Active"
            else:
                cluster_info = json.loads(os.environ.get("QUMULO_INFO"))
                storage_root_env = cluster_info[storage_type]["path"]
                storage_root = storage_root_env.strip("/")
                prepend_val = storage_root

            absolute_path = f"/{prepend_val}/{storage_filesystem_path}"
        AllocationView.set_billing_cycle(form_data)
        validate_filesystem_path_unique(absolute_path, storage_type)

        self.new_allocation = AllocationService.create_new_allocation(
            form_data, user, parent_allocation
        )
        self.success_id = self.new_allocation.get("allocation").id

        return super().form_valid(form)

    def get_success_url(self):
        if self.success_id is not None:
            return reverse(
                "qumulo:updateAllocation",
                kwargs={"allocation_id": self.success_id},
            )
        return super().get_success_url()
