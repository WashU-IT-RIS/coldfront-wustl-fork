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
        logger.debug(f"Filename: {self.filename}")

    def get_filename(self) -> str:
        return self.filename

    def get_report_header(self) -> str:
        if self.billing_cycle == "prepaid":
            additional_headers = (
                ",Prepaid Billing Date,Prepaid Expiration Date,Prepaid Time"
            )
        else:
            additional_headers = ""

        report_header = (
            """Submit Internal Service Delivery,,,,,,,,,,,,,,,,,,,,,,,,,,,
Area,All,,Business Process Parameters,Internal Service Delivery Data,,,,,,,Internal Service Delivery Line Data+,,,,,,,,,,,,,
Restrictions,Required,Optional,Optional,Optional,Optional,Required,Required,Required,Required,Optional,Required,Optional,Required,Optional,Optional,Optional,Optional,Optional,Required,Optional,Optional,Optional,Optional. May have multiples,Optional. May have multiples
Format,Text,Y/N,Y/N,Text,Y/N,Company_Reference_ID,Internal_Service_Provider_ID,Currency_ID,YYYY-MM-DD,Text,Text,Text,Number,Text,Spend_Category_ID,Number (22,2),UN_CEFACT_Common_Code_ID,Number (26,6),Number (18,3),Employee_ID,YYYY-MM-DD,Text,Cost_Center_Reference_ID,Fund_ID
Fields,Spreadsheet Key*,Add Only,Auto Complete,Internal Service Delivery ID,Submit,Company*,Internal Service Provider*,Currency*,Document Date*,Memo,Row ID**,Internal Service Delivery Line ID,Internal Service Delivery Line Number*,Item Description,Spend Category,Quantity,Unit of Measure,Unit Cost,Extended Amount*,Requester,Delivery Date,Memo,Cost Center"""
            + additional_headers
            + """,Fund,,,,USAGE,RATE,UNIT
"""
        )

        return report_header
