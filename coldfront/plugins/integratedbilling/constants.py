from enum import Enum


class BillingDataSources(Enum):
    ITSM = "ITSM"
    COLDFRONT = "Coldfront"


class StorageClusters(Enum):
    STORAGE1 = "Storage1"
    STORAGE2 = "Storage2"
    STORAGE3 = "Storage3"


class ServiceTiers(Enum):
    Active = 1
    Archive = 2
