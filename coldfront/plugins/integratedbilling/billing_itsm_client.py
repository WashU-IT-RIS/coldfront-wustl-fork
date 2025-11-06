from datetime import date
from typing import Any

from coldfront.plugins.integratedbilling.constants import ServiceRateTiers
from coldfront.plugins.qumulo.services.itsm.itsm_client_handler import ItsmClientHandler

ITSM_ATTRIBUTES_FOR_BILLING = [
    "id",
    "sponsor",
    "fileset_name",
    "service_rate_category",
    "amount",
    "funding_number",
    "exempt",
    "subsidized",
    "is_condo_group",
    "parent_id",
    "quota",
    "billing_cycle",
    "billing_contact",
    "status",
    "provision_usage_creation_date",
    "service_id",
]

ITSM_QUERY_KEY = "provision_usage_creation_date"  # Key for filtering billing data by creation date of usage records


class BillingItsmClient:
    def __init__(self, usage_date: date, tier: ServiceRateTiers = ServiceRateTiers.active) -> None:
        self.handler = ItsmClientHandler()
        self.usage_date = usage_date
        self.tier = tier

    def get_billing_usages(self) -> list[dict[str, Any]]:
        attributes = self.__get_attributes()
        filters = self.__get_filters()
        return self.handler.get_data(attributes, filters)

    # Private methods
    def __get_attributes(self) -> str:
        return ",".join(ITSM_ATTRIBUTES_FOR_BILLING)

    def __get_filters(self) -> str:
        usage_date = self.usage_date.strftime("%Y-%m-%d")
        itsm_service_id = self.tier.value
        return f'{{"{ITSM_QUERY_KEY}":"{usage_date}","service_id":{itsm_service_id}}}'
