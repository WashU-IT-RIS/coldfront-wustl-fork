from abc import ABC, abstractmethod

class Field(ABC):
    def __init__(self, value):
        self.__value = value
        super().__init__()

    @abstractmethod
    def is_valid(self):
        pass

    def get_coldfront_allocation_item(self):
        return {self.name_coldfront: self.value}

    @property
    def value(self):
        transformed_value = self.transformator()
        if transformed_value:
            return transformed_value
        return self.__value

    def transformator(self):
        return None

    @property
    def raw_value(self):
        return self.__value