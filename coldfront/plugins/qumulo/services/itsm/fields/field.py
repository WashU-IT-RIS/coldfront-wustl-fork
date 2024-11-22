from icecream import ic

import coldfront.plugins.qumulo.services.itsm.fields.transformers as value_transformers
import coldfront.plugins.qumulo.services.itsm.fields.validators as value_validators


class Field:
    def __init__(self, coldfront_definitions, itsm_value_field, value):
        self.coldfront_definitions = coldfront_definitions
        self._itsm_value_field = itsm_value_field
        self._coldfront_entity = coldfront_definitions["entity"]
        self._coldfront_attributes = coldfront_definitions["attributes"]
        self._value = value

    @property
    def value(self):
        return self.__transform_value()

    @property
    def entity(self):
        return self._coldfront_entity

    @property
    def attributes(self):
        return self._coldfront_attributes

    @property
    def entity_item(self):
        return {self.attributes[0].get("name"): self.value}

    @property
    def itsm_attribute_name(self):
        return self._itsm_value_field["attribute"]

    def validate(self):
        error_messages = []
        for attribute in self._coldfront_attributes:
            value = attribute["value"]
            name = attribute["name"]
            ic(name)
            if isinstance(value, dict):
                transforms = value["transforms"]

                to_be_validated = self._value or self.__get_default_value()
                if transforms is not None:
                    transforms_function = getattr(
                        value_transformers,
                        transforms,
                    )
                    to_be_validated = transforms_function(to_be_validated)

                for validator, conditions in value["validates"].items():
                    validator_function = getattr(
                        value_validators,
                        validator,
                    )
                    validation_message = validator_function(to_be_validated, conditions)
                    if validation_message:
                        error_messages.append(validation_message)
                    ic(to_be_validated)

            ic(value)
        ic(error_messages)
        return error_messages

    def __get_default_value(self):
        return self._itsm_value_field.get("defaults_to")

    def is_valid(self) -> bool:
        return bool(self.validate())

    def __transform_value(self):
        for attribute in self._coldfront_attributes:
            attribute_value = attribute["value"]
            if isinstance(attribute_value, dict):
                transforms = attribute_value["transforms"]

                value = self._value or self.__get_default_value()
                if transforms is not None:
                    transform_function = getattr(
                        value_transformers,
                        transforms,
                    )
                    value = transform_function(value)
                return value

    # Special getters
    def get_username(self):
        if self.entity != "user":
            return None

        username = None
        for attribute in self.attributes:
            if attribute["name"] == "username":
                username = self.value
        return username
