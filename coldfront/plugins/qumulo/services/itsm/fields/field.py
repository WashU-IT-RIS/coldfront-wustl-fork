class Field:
    def __init__(self, coldfront_definitions, itsm_values):
        self.coldfront_definitions = coldfront_definitions
        self.itsm_values = itsm_values
        self.entity = coldfront_definitions['entity']

 
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
