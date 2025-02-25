from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import FormView
from django.urls import reverse

from typing import Optional

import os

from coldfront.core.allocation.models import Allocation

from coldfront.plugins.qumulo.forms import AllocationForm
from coldfront.plugins.qumulo.utils.qumulo_api import QumuloAPI
from coldfront.plugins.qumulo.validators import validate_filesystem_path_unique
from coldfront.plugins.qumulo.utils.math_helper import bytes_to_terabytes


from coldfront.plugins.qumulo.services.allocation_service import AllocationService

from pathlib import PurePath
from datetime import date


class AllocationView(LoginRequiredMixin, FormView):
    form_class = AllocationForm
    template_name = "allocation.html"
    new_allocation = None
    success_id = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        file_system_stats_tb = self.__get_file_system_stats_in_tb()
        context["total_size_tb"] = file_system_stats_tb["total_size_tb"]
        context["free_size_tb"] = file_system_stats_tb["free_size_tb"]
        context["snapshot_size_tb"] = file_system_stats_tb["snapshot_size_tb"]
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

    def form_valid(
        self, form: AllocationForm, parent_allocation: Optional[Allocation] = None
    ):
        form_data = form.cleaned_data
        user = self.request.user
        storage_filesystem_path = form_data.get("storage_filesystem_path")
        is_absolute_path = PurePath(storage_filesystem_path).is_absolute()
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
                storage_root = os.environ.get("STORAGE2_PATH").strip("/")
                prepend_val = storage_root

            absolute_path = f"/{prepend_val}/{storage_filesystem_path}"
        AllocationView.set_billing_cycle(form_data)
        validate_filesystem_path_unique(absolute_path)

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

    def __get_file_system_stats_in_tb(self):
        file_system_stats = QumuloAPI().get_file_system_stats()
        total_size_tb = round(
            bytes_to_terabytes(int(file_system_stats.get("total_size_bytes"))), 2
        )
        free_size_tb = round(
            bytes_to_terabytes(int(file_system_stats.get("free_size_bytes"))), 2
        )
        snapshot_size_tb = round(
            bytes_to_terabytes(int(file_system_stats.get("snapshot_size_bytes"))), 2
        )
        return {
            "total_size_tb": total_size_tb,
            "free_size_tb": free_size_tb,
            "snapshot_size_tb": snapshot_size_tb,
        }
