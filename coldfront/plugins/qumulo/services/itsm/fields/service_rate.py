
from coldfront.plugins.qumulo.services.itsm.fields.field import Field 

from coldfront.plugins.qumulo.constants import STORAGE_SERVICE_RATES

class ServiceRate(Field):

    name_coldfront = "service_rate"
    name_itsm = "service_rate_category"

    def __init__(self, value):
        super().__init__(value)    

    def is_valid(self):
        # verify ITSM options
        return any([item for item in STORAGE_SERVICE_RATES if self.value in item])


"""
from coldfront.plugins.qumulo.services.itsm.fields.field import Field
from coldfront.plugins.qumulo.services.itsm.fields.service_rate import ServiceRate
cdfnt_field = ServiceRate("condo")
cdfnt_field.is_valid()
cdfnt_field.get_coldfront_allocation_item()
"""