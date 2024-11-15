from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import FormView
from django.urls import reverse

from typing import Optional

import os

from coldfront.core.allocation.models import Allocation

from coldfront.plugins.qumulo.forms import AllocationForm
from coldfront.plugins.qumulo.validators import validate_filesystem_path_unique
from coldfront.plugins.qumulo.services.allocation_service import AllocationService

from pathlib import PurePath


class AllocationView(LoginRequiredMixin, FormView):
    form_class = AllocationForm
    template_name = "allocation.html"
    new_allocation = None
    success_id = None

    def get_form_kwargs(self):
        kwargs = super(AllocationView, self).get_form_kwargs()
        kwargs["user_id"] = self.request.user.id
        return kwargs

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
