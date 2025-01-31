# from django.forms import Widget
from django.forms.widgets import Widget, ChoiceWidget, CheckboxSelectMultiple
import json
import pprint
import logging


class MultiSelectLookupInput(Widget):
    template_name = "multi_select_lookup_input.html"

    class Media:
        js = ("multi_select_lookup_input.js",)

    def value_from_datadict(self, data, files, name):
        try:
            getter = data.getlist
        except AttributeError:
            getter = data.get

        getter_return = getter(name)

        raw_string = (
            getter_return[0]
            if hasattr(getter_return, "__getitem__") and len(getter_return) > 0
            else ""
        )

        return raw_string.split(",")


class FilterableCheckBoxTableInput(ChoiceWidget):
    template_name = "filterable_checkbox_table_input.html"
    columns = []
    allow_multiple_selected = True

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        context["widget"]["options"] = context["widget"]["optgroups"][0][1]
        context["widget"]["columns"] = self.columns

        logging.warning(
            f"FilterableCheckBoxTableInput.get_context: {pprint.pformat(context)}"
        )

        return context

    class Media:
        js = ("filterable_checkbox_table_input.js",)
