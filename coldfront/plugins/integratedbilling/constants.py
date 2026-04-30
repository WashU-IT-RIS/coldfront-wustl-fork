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


QUERY_ATTRIBUTE = {
    "usage_date": {"itsm": "provision_usage_creation_date", "coldfront": "usage_date"},
    "service": {"itsm": "service_id", "coldfront": "service_id"},
    "dept_number": {"itsm": "department_number", "coldfront": "department_number"},
    "pi": {"itsm": "sponsor", "coldfront": "pi"},
    "service_rate_category": {
        "itsm": "service_rate_category",
        "coldfront": "service_rate_category",
    },
    "usage": {"itsm": "amount", "coldfront": "usage"},
}
