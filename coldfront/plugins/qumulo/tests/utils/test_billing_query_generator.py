from coldfront.plugins.qumulo.utils.eib_billing import EIBBilling
from coldfront.plugins.qumulo.utils.prepaid_billing import PrepaidBilling
from datetime import datetime, timezone

from coldfront.plugins.qumulo.utils.billing_query_generator import BillingGenerator
from django.test import TestCase

import re
import pdb


def _trawl_query_strings(original, compare):
    length = min(len(original), len(compare))

    for i in range(length):
        if original[i] != compare[i]:
            print(f"Diff at index: {i}")
            print(f"Original str at diff: {original[i-45:min(i+10, length)]}")
            print(f"Compare str at diff: {compare[i-45:min(i+10, length)]}")
            break


def _process_string(text):
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n+", "\n", text)
    return text


class TestBillingQueryGenerator(TestCase):
    def setUp(self) -> None:
        super().setUp()

    def test_prepaid_query_matches(self):

        prepaid_billing = PrepaidBilling(
            datetime.now(timezone.utc).strftime("%Y-%m-%d")
        )
        original = _process_string(prepaid_billing._get_prepaid_billing_query())

        args = dict()
        args["document_date"] = datetime.today().strftime("%m/%d/%Y")
        args["billing_month"] = prepaid_billing.billing_month
        args["delivery_date"] = prepaid_billing.delivery_date

        compare = _process_string(
            BillingGenerator.get_billing_query(
                args,
                "prepaid",
            )
        )

        self.assertEqual(original, compare)

    def test_monthly_query_matches(self):
        eib_billing = EIBBilling(datetime.now(timezone.utc).strftime("%Y-%m-%d"))
        original = _process_string(eib_billing._get_monthly_billing_query())
        args = dict()
        args["document_date"] = datetime.today().strftime("%m/%d/%Y")
        args["billing_month"] = eib_billing.billing_month
        args["delivery_date"] = eib_billing.delivery_date
        args["usage_date"] = eib_billing.usage_date
        compare = _process_string(
            BillingGenerator.get_billing_query(
                args,
                "monthly",
            )
        )

        self.assertEqual(original, compare)


# eib_billing = EIBBilling(datetime.now(timezone.utc).strftime("%Y-%m-%d"))
#        eib_billing.generate_monthly_billing_report()
