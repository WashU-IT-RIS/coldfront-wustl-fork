from django import forms


class TriggerMigrationsForm(forms.Form):
    allocation_name_search = (
        forms.CharField(
            label="Allocation Name",
            max_length=100,
            required=True,
            help_text="Type the allocation name here",
        ),
    )
    allocation_resource_name = (
        forms.ChoiceField(
            label="Resource Name",
            choices=[("Storage2", "Storage2"), ("Storage3", "Storage3")],
            required=True,
            help_text="Select the resource type for the allocation",
        ),
    )
