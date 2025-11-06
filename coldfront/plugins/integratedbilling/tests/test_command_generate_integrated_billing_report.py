from unittest import mock
from django.core.management import call_command, CommandError
from django.test import TestCase




@mock.patch(
    "coldfront.plugins.integratedbilling.report_generator.ReportGenerator.generate"
)
class TestGenerateIntegratedBillingReportCommand(TestCase):

    def setUp(self):
        self.args = []
        self.command_name = "generate_integrated_billing_report"

    def test_generate_integrated_billing_report_defaults(
        self, mock_generate: mock.MagicMock
    ):
        opts = {}
        call_command(self.command_name, *self.args, **opts)

    def test_generate_integrated_billing_report_with_options_active(
        self, mock_generate: mock.MagicMock
    ):
        opts = {
            "usage_date": "2025-11-01",
            "ingest_data": False,
            "tier": "active",
            "delivery_date": "2025-12-01",
            "dry_run": True,
        }
        call_command(self.command_name, *self.args, **opts)

    def test_generate_integrated_billing_report_with_options_archive(
        self, mock_generate: mock.MagicMock
    ):
        opts = {
            "usage_date": "2025-11-01",
            "ingest_data": False,
            "tier": "archive",
            "delivery_date": "2025-12-01",
            "dry_run": True,
        }
        call_command(self.command_name, *self.args, **opts)

    def test_generate_integrated_billing_report_with_wrong_usage_date(
        self, mock_generate: mock.MagicMock
    ):
        opts = {
            "usage_date": "2025-11-31",  # Invalid date
            "ingest_data": False,
            "tier": "archive",
            "delivery_date": "2025-12-01",
            "dry_run": True,
        }
        with self.assertRaises(
            CommandError, msg="Invalid usage_date format. Please use YYYY-MM-DD."
        ):
            call_command(self.command_name, *self.args, **opts)

    def test_generate_integrated_billing_report_with_wrong_delivery_date(
        self, mock_generate: mock.MagicMock
    ):
        opts = {
            "usage_date": "2025-11-01",  # Valid date
            "ingest_data": False,
            "tier": "archive",
            "delivery_date": "2025-12",  # Invalid date
            "dry_run": True,
        }
        with self.assertRaises(
            CommandError, msg="Invalid delivery_date format. Please use YYYY-MM-DD."
        ):
            call_command(self.command_name, *self.args, **opts)


# Note: These tests primarily ensure that the management command can be executed
# without raising exceptions. More detailed assertions can be added based on the
# specific behaviors and side effects of the command.


# Example taken and adapted from:
# Source - https://stackoverflow.com/questions/1286700/how-to-test-custom-django-admin-commands
# Posted by Jorge E. Cardona
# Retrieved 2025-11-06, License - CC BY-SA 4.0
# from django.core.management import call_command
# from django.test import TestCase
# class CommandsTestCase(TestCase):
#     def test_mycommand(self):
#         " Test my custom command."
#         args = []
#         opts = {}
#         call_command('mycommand', *args, **opts)
#         # Some Asserts.
