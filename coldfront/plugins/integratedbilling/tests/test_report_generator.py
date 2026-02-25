from coldfront.core.billing.factories import AllocationUsageFactory
from coldfront.core.billing.models import AllocationUsage
from io import StringIO
import sys
import json
from datetime import datetime, timezone
from freezegun import freeze_time
from unittest import mock
from django.test import TestCase
from coldfront.plugins.integratedbilling.factories import ServiceRateCategoryFactory
from coldfront.plugins.integratedbilling.report_generator import ReportGenerator

from coldfront.plugins.qumulo.tests.fixtures_usages import (
    create_coldfront_allocations_with_usages,
)


class TestReportGenerator(TestCase):

    def test_log_failed_subsidized_entries(self):
        # Create two allocations for the same PI, both subsidized, which should trigger the log
        pi_name = "Test PI"
        alloc1 = AllocationUsageFactory(sponsor_pi=pi_name, subsidized=True, tier="Active")
        alloc2 = AllocationUsageFactory(sponsor_pi=pi_name, subsidized=True, tier="Active")
        # Add a non-failing allocation for another PI
        AllocationUsageFactory(sponsor_pi="Other PI", subsidized=True, tier="Active")

        # Get all usages for the test PI
        usages = AllocationUsage.objects.filter(sponsor_pi=pi_name)

        # Patch stdout to capture print output
        captured_output = StringIO()
        sys_stdout = sys.stdout
        sys.stdout = captured_output
        try:
            # Create a ReportGenerator instance (date doesn't matter for this test)
            rg = ReportGenerator()
            # Call the private method directly
            rg._ReportGenerator__log_failed_subsidized_entries(usages)
        finally:
            sys.stdout = sys_stdout

        output = captured_output.getvalue()
        self.assertIn(f"PI {pi_name} has multiple subsidized allocations", output)
        self.assertIn("Allocation:", output)
        self.assertNotIn("Other PI", output)

    @mock.patch(
        "coldfront.plugins.integratedbilling.billing_itsm_client.ItsmClientHandler"
    )
    def setUp(self, mock_report_generator: mock.MagicMock) -> None:
        self.usage_date = datetime(2025, 10, 1, 18, 0, 0, tzinfo=timezone.utc)
        ServiceRateCategoryFactory(current_service_rate=True, archive_service=True)
        ServiceRateCategoryFactory(current_service_rate=True, active_service=True)

        # source data setup Coldfront allocations with usages recorded on the first day of the month
        with freeze_time(self.usage_date):
            create_coldfront_allocations_with_usages()

        # source data setup ITSM mock data
        with open(
            "coldfront/plugins/integratedbilling/static/mock_monthly_billing_data_current_month.json",
            "r",
        ) as file:
            report_generator = ReportGenerator(self.usage_date)
            mock_data = json.load(file)
            report_generator.client.handler.get_data.return_value = mock_data
            self.mock_report_generator = report_generator

    def test_generate_report_for_current_month_default(self):
        self.mock_report_generator.generate()
        # check that report file is created
        with open(
            f"/tmp/RIS-{self.mock_report_generator.delivery_month}-storage-{self.mock_report_generator.tier.name.lower()}-billing.csv",
            "r",
        ) as file:
            report_data = file.readlines()
            file.close()
        self.assertIsInstance(report_data, list)
        self.assertGreater(len(report_data), 0)
