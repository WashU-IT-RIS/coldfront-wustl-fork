from datetime import date, datetime
import json


from coldfront.plugins.qumulo.services.itsm.itsm_client import ItsmClientHandler


class BillingItsmClient:
    def __init__(self, billing_date: date = None):
        self.handler = ItsmClientHandler()
        today = datetime.now().date()
        self.billing_date = billing_date or today.replace(
            month=(today.month - 1 or 12), day=1
        )

    def get_billing_usages(self) -> str:
        attributes = self._get_attributes()
        filters = self._get_filters()
        return self.handler.get_data(attributes, filters)

    # Private methods
    def _get_attributes(self) -> str:
        itsm_attributes = "id,sponsor,fileset_name,service_rate_category,amount_tb,funding_number,exempt,subsidized,is_condo_group,parent_id,quota,billing_cycle,status"
        return itsm_attributes

    def _get_filters(self) -> str:
        itsm_active_allocation_service_id = 1 # just the active allocation service for now
        key = "provision_usage_creation_date"
        billing_date = self.billing_date.strftime("%Y-%m-%d")
        return f'{{"{key}":"{billing_date}","service_id":{itsm_active_allocation_service_id}}}'
