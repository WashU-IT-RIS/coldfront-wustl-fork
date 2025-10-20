import json

from datetime import datetime
from django.test import TestCase
from unittest import mock

from coldfront.plugins.integratedbilling.billing_itsm_client import BillingItsmClient
from coldfront.plugins.integratedbilling.itsm_usage_ingestor import (
    ItsmUsageIngestor,
)
from coldfront.plugins.qumulo.tests.utils.mock_data import build_models


class TestBillingItsmClient(TestCase):

    @mock.patch(
        "coldfront.plugins.integratedbilling.billing_itsm_client.ItsmClientHandler"
    )
    def setUp(self, mock_billing_itsm_client: mock.MagicMock) -> None:
        # fixed current date for testing and simulating when report is generated
        build_models()
        current_date = datetime(2025, 10, 4).date()
        self.default_billing_date = current_date.replace(day=1)
        billing_itsm_client = BillingItsmClient()
        with open(
            "coldfront/plugins/integratedbilling/static/mock_monthly_billing_data_current_month.json",
            "r",
        ) as file:
            mock_data = json.load(file)
            billing_itsm_client.handler.get_data.return_value = mock_data
            self.mock_billing_itsm_client = billing_itsm_client

    def test_itsm_usage_data_ingestion(self):
        client = BillingItsmClient()
        usage_ingestor = ItsmUsageIngestor(client)
        empty_list = []
        self.assertIsNot(usage_ingestor._ItsmUsageIngestor__ingest_usages(), empty_list)
        service_provision_usage = usage_ingestor._ItsmUsageIngestor__ingest_usages()[0]
        self.assertIsInstance(service_provision_usage, dict)
        self.assertIsNot(service_provision_usage, {})
