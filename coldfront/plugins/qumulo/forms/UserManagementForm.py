from django import forms

from coldfront.core.field_of_science.models import FieldOfScience
from coldfront.core.allocation.models import Allocation

from coldfront.plugins.qumulo.fields import ADUserField
from coldfront.plugins.qumulo.widgets import FilterableCheckBoxTableInput


class UserManagementForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["allocations"].choices = self.get_allocations()
        self.fields["allocations"].widget.columns = [
            "id",
            "resource_name",
            "allocation_status",
            "file_path",
        ]

    users = ADUserField(
        label="Users",
        initial="",
    )

    allocations = forms.TypedMultipleChoiceField(
        label="Allocations",
        widget=FilterableCheckBoxTableInput,
    )

    def build_allocation_choice(self, allocation: Allocation):
        allocation_choice = {}

        allocation_choice["id"] = allocation.pk
        allocation_choice["resource_name"] = allocation.resources.last().name
        allocation_choice["allocation_status"] = allocation.status.name
        allocation_choice["file_path"] = allocation.get_attribute(
            "storage_filesystem_path"
        )

        return allocation_choice

    def get_allocations(self):
        allocations = list(Allocation.objects.filter(resources__name="Storage2"))
        allocation_choices = list(
            map(
                self.build_allocation_choice,
                allocations,
            )
        )

        return map(
            lambda allocation: (
                allocation["id"],
                allocation,
            ),
            allocation_choices,
        )
