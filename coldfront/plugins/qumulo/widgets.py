from django.forms import Widget
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


class FilterableCheckBoxTableInput(Widget):
    template_name = "filterable_checkbox_table_input.html"

    def value_from_datadict(self, data, files, name):
        logger.warning(
            f"FilterableCheckBoxTableInput.value_from_datadict() called with data={pprint.pformat(data)}, files={pprint.pformat(files)}, name={name}"
        )
        return super().value_from_datadict(data, files, name)

    def render(self, name, value, attrs=..., renderer=...):
        logger.warning(
            f"FilterableCheckBoxTableInput.render() called with name={name}, value={value}, attrs={attrs}"
        )
        return super().render(name, value, attrs, renderer)

    # class Media:
    #     js = ("filterable_checkbox_table_input.js",)
