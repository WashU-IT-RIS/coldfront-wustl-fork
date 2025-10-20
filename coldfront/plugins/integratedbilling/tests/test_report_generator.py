import json
from unittest import mock
from django.test import TestCase
from coldfront.plugins.integratedbilling.report_generator import ReportGenerator
from coldfront.plugins.qumulo.tests.utils.mock_data import build_models


class TestReportGenerator(TestCase):

    @mock.patch(
        "coldfront.plugins.integratedbilling.billing_itsm_client.ItsmClientHandler"
    )
    def setUp(self, mock_report_generator: mock.MagicMock) -> None:
        build_models()

        with open(
            "coldfront/plugins/integratedbilling/static/mock_monthly_billing_data_current_month.json",
            "r",
        ) as file:
            report_generator = ReportGenerator()
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
            report_data = json.load(file)
            file.close()

        self.assertIsInstance(report_data, list)
        self.assertGreater(len(report_data), 0)
        first_row = report_data[0]
        self.assertIsInstance(first_row, dict)
        self.assertIn("date", first_row)
        self.assertIn("storage_cluster", first_row)
        self.assertIn("usage_tb", first_row)
            

