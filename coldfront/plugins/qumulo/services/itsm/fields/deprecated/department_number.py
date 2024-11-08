from coldfront.plugins.qumulo.services.itsm.fields.field import Field 

# DEPERECATED: 
class DepartmentNumber(Field):

    name_coldfront = "department_number"
    name_itsm = "department_number"

    def __init__(self, value):
        super().__init__(value)    

    def is_valid(self):
        return len(self.value) < 128


"""
from coldfront.plugins.qumulo.services.itsm.fields.field import Field
from coldfront.plugins.qumulo.services.itsm.fields.department_number import DepartmentNumber
cdfnt_field = DepartmentNumber("474747")
cdfnt_field.is_valid()
cdfnt_field.get_coldfront_allocation_item()
"""