# from django.forms import Widget
from django.forms.widgets import Widget, ChoiceWidget, CheckboxSelectMultiple
import logging
import pprint

logger = logging.getLogger(__name__)


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
    allow_multiple_selected = True
    # input_type = "checkbox"

    def get_context(self, name, value, attrs):
        return_value = super().get_context(name, value, attrs)

        logger.warning(
            f"FilterableCheckBoxTableInput.get_context() called with name={name}, value={value}, attrs={attrs}\n\nreturn_value={pprint.pformat(return_value)}"
        )

        return return_value

    def render(self, name, value, attrs=..., renderer=...):
        logger.warning(
            f"FilterableCheckBoxTableInput.render() called with choices={pprint.pformat(self.choices)}, name={name}, value={value}, attrs={attrs}"
        )
        return super().render(name, value, attrs, renderer)

    # class Media:
    #     js = ("filterable_checkbox_table_input.js",)
