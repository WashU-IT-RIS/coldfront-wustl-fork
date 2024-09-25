import os
from django import forms

from coldfront.plugins.qumulo.validators import (
    validate_ad_users,
    validate_filesystem_path_unique,
    validate_parent_directory,
    validate_storage_root,
)

from coldfront.plugins.qumulo.widgets import MultiSelectLookupInput

from pathlib import PurePath


class ADUserField(forms.Field):
    widget = MultiSelectLookupInput
    default_validators = [validate_ad_users]

    def prepare_value(self, value: list[str]):
        value_str = ",".join(value)

        return value_str

    def to_python(self, value: list[str]):
        return list(filter(lambda element: len(element), value))


class StorageFileSystemPathField(forms.CharField):
    default_validators = [
        validate_storage_root,
        validate_parent_directory,
        validate_filesystem_path_unique,
    ]

    def run_validators(self, value: str) -> None:
        is_absolute_path = PurePath(value).is_absolute()
        if not is_absolute_path:
            storage_root = os.environ.get("STORAGE2_PATH").strip("/")
            full_path = f"/{storage_root}/{value}"
        else:
            full_path = value

        return super().run_validators(full_path)
