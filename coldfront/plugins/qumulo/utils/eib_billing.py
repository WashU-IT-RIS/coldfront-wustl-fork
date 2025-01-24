import logging
import csv
import re
from datetime import datetime, timedelta
from django.db import connection

from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttribute,
    AllocationAttributeType,
)

from coldfront.plugins.qumulo.utils.billing_report import BillingReport

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

YYYY_MM_DD = "%Y-%m-%d"


class EIBBilling(BillingReport):
    def __init__(self, timestamp):
        super().__init__("monthly", timestamp)

    def _get_monthly_billing_query(self) -> str:
        # The date when the billing report was generated
        document_date = datetime.today().strftime("%m/%d/%Y")

        monthly_billing_query = self.get_monthly_billing_query_template() % (
            document_date,
            self.billing_month,
            self.delivery_date,
            self.usage_date,
        )
        return monthly_billing_query

    def generate_monthly_billing_report(self) -> bool:
        args = dict()
        args["document_date"] = datetime.today().strftime("%m/%d/%Y")
        args["billing_month"] = self.billing_month
        args["delivery_date"] = self.delivery_date
        args["usage_date"] = self.usage_date

        monthly_billing_query = super().get_query(args, "monthly")

        super().generate_report(monthly_billing_query)
