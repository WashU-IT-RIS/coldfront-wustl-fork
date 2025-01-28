from django import forms

from coldfront.core.field_of_science.models import FieldOfScience
from coldfront.core.allocation.models import Allocation

from coldfront.plugins.qumulo.fields import ADUserField
from coldfront.plugins.qumulo.widgets import FilterableCheckBoxTableInput

import logging


class UserManagementForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["allocations"].choices = self.get_allocations()

    users = ADUserField(
        label="Users",
        initial="",
    )

    allocations = forms.TypedMultipleChoiceField(
        label="Allocations",
        widget=FilterableCheckBoxTableInput,
    )

    def get_allocations(self):
        allocations = Allocation.objects.filter(resources__name="Storage2")

        return map(
            lambda allocation: (
                allocation.id,
                allocation,
            ),
            Allocation.objects.filter(resources__name="Storage2"),
        )

    def get_fos_choices(self):
        return map(lambda fos: (fos.id, fos.description), FieldOfScience.objects.all())
