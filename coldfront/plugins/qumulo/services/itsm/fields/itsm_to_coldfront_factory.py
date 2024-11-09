import yaml

from coldfront.plugins.qumulo.services.itsm.fields.field import Field

with open(
    "coldfront/plugins/qumulo/static/itsm_to_coldfront_map.yaml", "r"
) as file:
    itsm_to_coldfront_map = yaml.safe_load(file)
    field_map = itsm_to_coldfront_map["itsm_to_coldfront_map"]
    field_items = {key: value for key, value in field_map.items() if value is not None}
    itsm_attributes = field_items.keys()


class ItsmToColdfrontFactory:

    @staticmethod
    def get_fields(itsm_allocation):
        fields = []
        for item in field_items.values():
            itsm_value_field = item["itsm_value"]
            for coldfront_definitions in item["coldfront"]:
                value = itsm_allocation.get(itsm_value_field["attribute"])
                fields.append(Field(coldfront_definitions, itsm_value_field, value))
        return fields

"""
with open(
    "coldfront/plugins/qumulo/services/itsm/fields/itsm_to_coldfront_map.yaml", "r"
) as file:
    itsm_to_coldfront_map = yaml.safe_load(file)
    field_map = itsm_to_coldfront_map["itsm_to_coldfront_map"]
    field_items = {key: value for key, value in field_map.items() if value is not None}
    # Required by the ITSM Client
    itsm_attributes = field_items.keys()
    for item in field_items.values():
        for coldfront_definitions in item["coldfront"]:
            entity = coldfront_definitions["entity"]
            print(entity)
            attributes = coldfront_definitions["attributes"]
            for attribute in attributes:
                name_attribute = attribute["name"]
                value_attribute = attribute["value"]
                if isinstance(value_attribute, dict):
                    type = value_attribute["type"]
                    transforms = value_attribute["transforms"]
                    validates = value_attribute["validates"]
                    foreign_key = value_attribute.get("foreign_key")
                    print(type)
                    print(transforms)
                    print(validates)
                else:
                    print(name_attribute, "=", value_attribute)
    for item in field_items.values():
        itsm_value = item["itsm_value"]
        print("---------------------")
        print(itsm_value["attribute"])
        print(itsm_value["type"])
        print(itsm_value.get("nulls"))
        print(itsm_value.get("defaults_to"))
"""
