import json

from datetime import datetime, timedelta
from django.test import TestCase
from unittest import mock

from coldfront.plugins.integratedbilling.billing_itsm_client import BillingItsmClient
from coldfront.plugins.integratedbilling.tests.fixtures import (
    ITSM_ATTRIBUTES_FOR_BILLING,
)


class TestBillingItsmClient(TestCase):

    @mock.patch(
        "coldfront.plugins.integratedbilling.billing_itsm_client.ItsmClientHandler"
    )
    def setUp(self, mock_billing_itsm_client: mock.MagicMock) -> None:
        # fixed current date for testing and simulating when report is generated
        current_date = datetime(2025, 10, 4).date()
        self.usage_date = current_date.replace(day=1)
        billing_itsm_client = BillingItsmClient()
        with open(
            "coldfront/plugins/integratedbilling/static/mock_monthly_billing_data_current_month.json",
            "r",
        ) as file:
            mock_data = json.load(file)
            billing_itsm_client.handler.get_data.return_value = mock_data
            self.mock_billing_itsm_client = billing_itsm_client

    def test_presence_of_billing_attributes(self):
        billing_itsm_client = self.mock_billing_itsm_client
        empty_list = []
        data = billing_itsm_client.get_billing_usages()
        self.assertIsNot(data, empty_list)
        service_provision_usage = data[0]
        self.assertIsInstance(service_provision_usage, dict)
        self.assertIsNot(service_provision_usage, {})
        for key in ITSM_ATTRIBUTES_FOR_BILLING:
            self.assertIn(key, service_provision_usage.keys())

    def test_default_billing_attributes(self):
        billing_itsm_client = self.mock_billing_itsm_client
        data = billing_itsm_client.get_billing_usages()
        service_provision_usage = data[0]
        for key in [
            "_service_provision",
            "_provision_usage",
        ]:
            self.assertIn(key, service_provision_usage.keys())

    def test_data_should_not_be_empty_for_current_month(self):
        billing_itsm_client = self.mock_billing_itsm_client
        empty_list = []
        data = billing_itsm_client.get_billing_usages()
        self.assertIsNot(data, empty_list)
        service_provision_usage = data[0]
        self.assertIsInstance(service_provision_usage, dict)
        self.assertIsNot(service_provision_usage, {})

    def test_billing_date_is_first_of_month(self):
        billing_itsm_client = self.mock_billing_itsm_client
        data = billing_itsm_client.get_billing_usages()
        service_provision_usage = data[0]
        provision_usage_creation_date = datetime.fromisoformat(
            service_provision_usage.get("provision_usage_creation_date").replace(
                "Z", "+00:00"
            )
        ).date()
        self.assertEqual(self.usage_date, provision_usage_creation_date)

    @mock.patch(
        "coldfront.plugins.integratedbilling.billing_itsm_client.ItsmClientHandler"
    )
    def test_data_should_not_be_empty_for_previous_month(
        self, mock_billing_itsm_client: mock.MagicMock
    ):
        first_day_previous_month_date = (
            self.usage_date.replace(day=1) - timedelta(days=1)
        ).replace(day=1)
        billing_itsm_client = BillingItsmClient(first_day_previous_month_date)

        with open(
            "coldfront/plugins/integratedbilling/static/mock_monthly_billing_data_previous_month.json",
            "r",
        ) as file:
            mock_data = json.load(file)
            billing_itsm_client.handler.get_data.return_value = mock_data

        data = billing_itsm_client.get_billing_usages()
        service_provision_usage = data[0]
        provision_usage_creation_date = datetime.fromisoformat(
            service_provision_usage.get("provision_usage_creation_date").replace(
                "Z", "+00:00"
            )
        ).date()
        self.assertNotEqual(self.usage_date, provision_usage_creation_date)
        self.assertEqual(first_day_previous_month_date, provision_usage_creation_date)
