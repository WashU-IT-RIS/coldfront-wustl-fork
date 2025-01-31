import os
from django import forms

from coldfront.plugins.qumulo.validators import (
    validate_filesystem_path_unique,
    validate_parent_directory,
    validate_relative_path,
)

from coldfront.plugins.qumulo.widgets import (
    MultiSelectLookupInput,
    FilterableCheckBoxTableInput,
)


class ADUserField(forms.Field):
    widget = MultiSelectLookupInput
    default_validators = []

    def prepare_value(self, value: list[str]):
        value_str = ",".join(value)

        return value_str

    def to_python(self, value: list[str]):
        return list(filter(lambda element: len(element), value))


class StorageFileSystemPathField(forms.CharField):
    default_validators = [
        validate_relative_path,
        validate_parent_directory,
        validate_filesystem_path_unique,
    ]


# class FilterableCheckBoxTableField(forms.TypedMultipleChoiceField):
#     widget = FilterableCheckBoxTableInput

#     def __init__(self, *, choices=(), **kwargs):
#         super().__init__(**kwargs)
#         self.columns = []
