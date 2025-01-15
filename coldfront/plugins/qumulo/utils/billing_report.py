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

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

YYYY_MM_DD = "%Y-%m-%d"


class BillingReport:
    def __init__(
        self, billing_cycle, today=datetime.today().replace(day=1).strftime(YYYY_MM_DD)
    ):
        self.billing_cycle = billing_cycle
        if self.billing_cycle == "prepaid":
            future_date = datetime.strptime(today, YYYY_MM_DD) + relativedelta(months=1)
            self.usage_date = future_date.strftime(YYYY_MM_DD)
            self.delivery_date = (
                (datetime.strptime(self.usage_date, YYYY_MM_DD).replace(day=1))
                .replace(day=1)
                .strftime(YYYY_MM_DD)
            )
        else:
            self.usage_date = today
            self.delivery_date = (
                (
                    datetime.strptime(self.usage_date, YYYY_MM_DD).replace(day=1)
                    - timedelta(1)
                )
                .replace(day=1)
                .strftime(YYYY_MM_DD)
            )
        logger.debug(f"Usage Date: {self.usage_date}")
        logger.debug(f"Delivery Date: {self.delivery_date}")
        self.billing_month = datetime.strptime(self.delivery_date, YYYY_MM_DD).strftime(
            "%B"
        )
        self.filename = f"/tmp/RIS-{self.billing_month}-storage2-{self.billing_cycle}-active-billing.csv"

    def get_filename(self) -> str:
        return self.filename
