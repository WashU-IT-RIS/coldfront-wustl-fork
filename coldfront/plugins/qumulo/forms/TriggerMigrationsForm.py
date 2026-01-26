from django import forms

from coldfront.core.resource.models import Resource
from coldfront.plugins.qumulo.constants import DEFAULT_STORAGE_TYPE


class TriggerMigrationsForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["allocation_resource_name"].initial = Resource.objects.get(
            name=DEFAULT_STORAGE_TYPE
        ).name
        self.fields["allocation_resource_name"].choices = [
            (resource.name, resource.name)
            for resource in Resource.objects.filter(
                resource_type__name="Storage", is_available=True
            )
        ]

    allocation_name_search = forms.CharField(
        label="Allocation Name",
        max_length=100,
        required=True,
        help_text="the ITSM allocation name to migrate, for example, /vol/rdcw2/allocation_name",
    )

    allocation_resource_name = forms.ChoiceField(
        label="Resource Name",
        required=True,
        help_text="the Coldfront storage resource name to migrate allocations into",
    )
