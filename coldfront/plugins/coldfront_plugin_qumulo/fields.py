from django import forms

from coldfront_plugin_qumulo.validators import validate_ad_users

from coldfront_plugin_qumulo.widgets import MultiSelectLookupInput


class ADUserField(forms.Field):
    widget = MultiSelectLookupInput
    default_validators = [validate_ad_users]

    def prepare_value(self, value: list[str]):
        value_str = ",".join(value)

        return value_str

    def to_python(self, value: list[str]):
        return list(filter(lambda element: len(element), value))
