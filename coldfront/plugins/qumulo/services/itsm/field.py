class Field:
    def __init__(self, coldfront_entity, coldfront_name, itsm_name, value):
        self.coldfront_entity = coldfront_entity
        self.coldfront_name = coldfront_name
        self.itsm_name = itsm_name
        self.value = value
        self.transformator = None
        self.validator  = None

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

