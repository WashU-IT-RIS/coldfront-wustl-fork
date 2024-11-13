from coldfront.plugins.qumulo.services.itsm.fields.deprecated.field import Field


# DEPERECATED:
class StorageQuota(Field):

    name_coldfront = "storage_quota"
    name_itsm = "quota"

    def __init__(self, value):
        super().__init__(value)

    def is_valid(self):
        return self.value > 0 and self.value <= 2000

    def tranformator(self):
        value = int(self.raw_value[:-1])
        if self.raw_value[-1] == "T":
            return value

        return value / 100


"""
from coldfront.plugins.qumulo.services.itsm.fields.field import Field
from coldfront.plugins.qumulo.services.itsm.fields.storage_quota import CosStorageQuotatCenter 
cdfnt_field = StorageQuota("474747")
cdfnt_field.is_valid()
cdfnt_field.get_coldfront_allocation_item()
"""
