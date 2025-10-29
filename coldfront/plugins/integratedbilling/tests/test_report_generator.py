from datetime import datetime, timezone
from freezegun import freeze_time
import json
from unittest import mock
from django.test import TestCase
from coldfront.plugins.integratedbilling.factories import ServiceRateCategoryFactory
from coldfront.plugins.integratedbilling.report_generator import ReportGenerator

from coldfront.plugins.integratedbilling.tests.fixtures import (
    create_coldfront_allocations_with_usages,
)


class TestReportGenerator(TestCase):

    @mock.patch(
        "coldfront.plugins.integratedbilling.billing_itsm_client.ItsmClientHandler"
    )
    def setUp(self, mock_report_generator: mock.MagicMock) -> None:
        self.ingestion_date = datetime(2025, 10, 1, 18, 0, 0, tzinfo=timezone.utc)
        self.report_date = datetime(2025, 10, 1, 18, 0, 0, tzinfo=timezone.utc)
        ServiceRateCategoryFactory(current_service_rate=True, archive_service=True)
        ServiceRateCategoryFactory(current_service_rate=True, active_service=True)

        # source data setup Coldfront allocations with usages
        with freeze_time(self.ingestion_date):
            create_coldfront_allocations_with_usages()

        # source data setup ITSM mock data
        with open(
            "coldfront/plugins/integratedbilling/static/mock_monthly_billing_data_current_month.json",
            "r",
        ) as file:
            report_generator = ReportGenerator(self.report_date)
            mock_data = json.load(file)
            report_generator.client.handler.get_data.return_value = mock_data
            self.mock_report_generator = report_generator

    def test_generate_report_for_current_month_default(self):
        self.mock_report_generator.generate()
        # check that report file is created
        with open(
            f"billing_report_{self.mock_report_generator.client.usage_date}.csv",
            "r",
        ) as file:
            report_data = file.readlines()
            file.close()

        self.assertIsInstance(report_data, list)
        self.assertGreater(len(report_data), 0)
        first_row = report_data[0]
        self.assertIsInstance(first_row, dict)
        self.assertIn("date", first_row)
        self.assertIn("storage_cluster", first_row)
        self.assertIn("usage_tb", first_row)
