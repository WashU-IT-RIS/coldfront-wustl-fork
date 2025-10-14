from datetime import date, datetime
from typing import Any

from coldfront.plugins.qumulo.services.itsm.itsm_client_handler import ItsmClientHandler

ITSM_ATTRIBUTES_FOR_BILLING = [
    "id",
    "sponsor",
    "fileset_name",
    "service_rate_category",
    "amount",
    "amount_tb",
    "funding_number",
    "exempt",
    "subsidized",
    "is_condo_group",
    "parent_id",
    "quota",
    "billing_cycle",
    "status",
    "provision_usage_creation_date",
]


# helper function to get the default billing date (first day of the current month)
def _get_default_billing_date() -> date:
    today = datetime.now().date()
    return today.replace(day=1)


ITSM_ACTIVE_ALLOCATION_SERVICE_ID = (
    1  # This should match the service ID in ITSM for active allocations
)
ITSM_QUERY_KEY = "provision_usage_creation_date"  # Key for filtering billing data by creation date of usage records


class BillingItsmClient:
    def __init__(self, billing_date: date = None):
        self.handler = ItsmClientHandler()
        self.billing_date = billing_date or _get_default_billing_date()

    def get_billing_usages(self) -> list[dict[str, Any]]:
        attributes = self.__get_attributes()
        filters = self.__get_filters()
        return self.handler.get_data(attributes, filters)

    # Private methods
    def __get_attributes(self) -> str:
        return ",".join(ITSM_ATTRIBUTES_FOR_BILLING)

    def __get_filters(self) -> str:
        billing_date = self.billing_date.strftime("%Y-%m-%d")
        return f'{{"{ITSM_QUERY_KEY}":"{billing_date}","service_id":{ITSM_ACTIVE_ALLOCATION_SERVICE_ID}}}'
