import logging
import csv
import re
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
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


class PrepaidBilling(BillingReport):
    def __init__(self, timestamp):
        super().__init__("prepaid", timestamp)

    def _get_prepaid_billing_query(self) -> str:
        # The date when the billing report was generated
        document_date = datetime.today().strftime("%m/%d/%Y")

        prepaid_billing_query = self.get_prepaid_billing_query_template() % (
            document_date,
            self.billing_month,
            self.delivery_date,
            self.delivery_date,
        )
        return prepaid_billing_query

    def generate_prepaid_billing_report(self) -> bool:
        args = dict()
        args["document_date"] = datetime.today().strftime("%m/%d/%Y")
        args["billing_month"] = self.billing_month
        args["delivery_date"] = self.delivery_date

        prepaid_billing_query = super().get_query(args, "prepaid")
        super().generate_report(prepaid_billing_query)
