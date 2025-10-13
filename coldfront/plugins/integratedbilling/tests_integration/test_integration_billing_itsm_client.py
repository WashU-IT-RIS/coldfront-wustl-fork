from datetime import datetime, timedelta
import json
from django.test import TestCase, tag

from coldfront.plugins.integratedbilling.billing_itsm_client import BillingItsmClient
from coldfront.plugins.integratedbilling.tests.fixtures import (
    ITSM_ATTRIBUTES_FOR_BILLING,
)


class TestIntegrationBillingItsmClient(TestCase):

    def setUp(self) -> None:
        today = datetime.now().date()
        self.default_billing_date = today.replace(day=1)
        self.billing_itsm_client = BillingItsmClient()

    @tag("integration")
    def test_presence_of_billing_attributes(self):
        billing_itsm_client = self.billing_itsm_client
        empty_list = []
        data = billing_itsm_client.get_billing_usages()
        self.assertIsNot(data, empty_list)
        service_provision_usage = data[0]
        self.assertIsInstance(service_provision_usage, dict)
        for key in ITSM_ATTRIBUTES_FOR_BILLING:
            self.assertIn(key, service_provision_usage.keys())

    @tag("integration")
    def test_default_billing_attributes(self):
        billing_itsm_client = self.billing_itsm_client
        data = billing_itsm_client.get_billing_usages()
        service_provision_usage = data[0]
        for key in [
            "provision_usage_creation_date",
            "_service_provision",
            "_provision_usage",
        ]:
            self.assertIn(key, service_provision_usage.keys())

    @tag("integration")
    def test_data_should_not_be_empty_for_current_month(self):
        billing_itsm_client = self.billing_itsm_client
        empty_list = []
        data = billing_itsm_client.get_billing_usages()
        self.assertIsNot(data, empty_list)
        service_provision_usage = data[0]
        self.assertIsInstance(service_provision_usage, dict)
        self.assertIsNot(service_provision_usage, {})

    @tag("integration")
    def test_billing_date_is_first_of_month(self):
        billing_itsm_client = self.billing_itsm_client
        data = billing_itsm_client.get_billing_usages()
        service_provision_usage = data[0]
        provision_usage_creation_date = datetime.fromisoformat(
            service_provision_usage.get("provision_usage_creation_date").replace(
                "Z", "+00:00"
            )
        ).date()
        self.assertEqual(self.default_billing_date, provision_usage_creation_date)

    @tag("integration")
    def test_data_should_not_be_empty_for_previous_month_(self):
        first_day_previous_month_date = (
            self.default_billing_date.replace(day=1) - timedelta(days=1)
        ).replace(day=1)
        billing_itsm_client = BillingItsmClient(first_day_previous_month_date)
        data = billing_itsm_client.get_billing_usages()
        service_provision_usage = data[0]
        provision_usage_creation_date = datetime.fromisoformat(
            service_provision_usage.get("provision_usage_creation_date").replace(
                "Z", "+00:00"
            )
        ).date()
        self.assertNotEqual(self.default_billing_date, provision_usage_creation_date)
        self.assertEqual(first_day_previous_month_date, provision_usage_creation_date)
