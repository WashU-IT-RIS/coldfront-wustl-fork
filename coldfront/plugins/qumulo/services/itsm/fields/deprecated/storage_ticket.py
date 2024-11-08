import re

from coldfront.plugins.qumulo.services.itsm.fields.field import Field 

# DEPERECATED: 
class StorageTicket(Field):

    name_coldfront = "storage_ticket"
    name_itsm = "service_desk_ticket_number"

    def __init__(self, value):
        super().__init__(value)

    def is_valid(self):
        ticket = self.value
        if re.match("\d+$", ticket):
            return True
        if re.match("ITSD-\d+$", ticket, re.IGNORECASE):
            return True
        raise Exception(
            f"Service desk ticket \"{ticket}\" must have format: ITSD-12345 or 12345",
        )


"""
from coldfront.plugins.qumulo.services.itsm.fields.field import Field
from coldfront.plugins.qumulo.services.itsm.fields.storage_ticket import StorageTicket 
cdfnt_field = StorageTicket("ITSD-1")
cdfnt_field.is_valid()
cdfnt_field.get_coldfront_allocation_item()
"""