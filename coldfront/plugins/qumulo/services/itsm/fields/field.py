from icecream import ic

import coldfront.plugins.qumulo.services.itsm.fields.transformers as value_transformers
import coldfront.plugins.qumulo.services.itsm.fields.validators as value_validators


class Field:
    def __init__(self, coldfront_definitions, itsm_value_field, value):
        self.coldfront_definitions = coldfront_definitions
        self.itsm_value_field = itsm_value_field
        self._coldfront_entity = coldfront_definitions["entity"]
        self._coldfront_attributes = coldfront_definitions["attributes"]
        self._value = value
        # ic(coldfront_definitions)
        # ic(itsm_value_field)
        # ic(value)

    @property
    def value(self):
        return self._value

    @property
    def entity(self):
        return self._coldfront_entity

    @property
    def attributes(self):
        return self._coldfront_attributes

    def validate(self):
        valid = True
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
                    valid = valid and validator_function(to_be_validated, conditions)
                    ic(to_be_validated)

            valid = valid and value is not None
            ic(value)
        ic(valid)
        print("----------")
        return valid

    def __get_default_value(self):
        return self.itsm_value_field.get("defaults_to")

    def is_valid(self) -> bool:
        return self.validate()

    # TODO: create coldfront entities

    """
    @property
    def itsm_name(self):
        return self.name_itsm

    @property
    def coldfront_name(self):
        return self.name_coldfront
    
    @property
    def coldfront_entity(self):
        return self.coldfront_entity

    def get_value(self):
        if self.transformator is None:
            self.validator is None or self.validator(self.value)
            return self.value

        transformed_value = self.transformator(self.value)
        self.validator is None or self.validator(transformed_value)
        return transformed_value

    def get_coldfront_allocation_item(self):
        return {self.name_coldfront: self.value}

    @property
    def raw_value(self):
        return self.value

    def set_transformator(self, transformator):
        self.transformator = transformator

    def set_validator(self, validator):
        self.validator = validator

    def is_valid(self):
        if self.transformator is None:
            try:
                self.validator is None or self.validator(self.value)
            except:
                return False
            return True

        transformed_value = self.transformator(self.value)
        try:
            self.validator is None or self.validator(transformed_value)
        except:
            return False
        return True
    """
