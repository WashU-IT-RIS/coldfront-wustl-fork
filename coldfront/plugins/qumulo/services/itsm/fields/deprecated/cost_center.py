from coldfront.plugins.qumulo.services.itsm.fields.deprecated.field import Field


# DEPERECATED:
class CostCenter(Field):

    name_coldfront = "cost_center"
    name_itsm = "funding_number"

    def __init__(self, value):
        super().__init__(value)

    def is_valid(self):
        return len(self.value) < 128


"""
from coldfront.plugins.qumulo.services.itsm.fields.field import Field
from coldfront.plugins.qumulo.services.itsm.fields.cost_center import CostCenter 
st = CostCenter("474747")
st.is_valid()
"""
