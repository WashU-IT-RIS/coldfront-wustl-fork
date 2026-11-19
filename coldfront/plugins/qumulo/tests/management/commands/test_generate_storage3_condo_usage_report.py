from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.test import TestCase

from coldfront.plugins.qumulo.management.commands.add_scheduled_generate_storage3_condo_usage_report_monthly import (
    generate_storage3_condo_usage_report,
    get_billing_contact_emails,
)

MODULE = "coldfront.plugins.qumulo.management.commands.add_scheduled_generate_storage3_condo_usage_report_monthly"


def _allocation(pk, billing_contact):
    allocation = MagicMock()
    allocation.pk = pk
    allocation.get_attribute.side_effect = lambda name: (
        billing_contact if name == "billing_contact" else None
    )
    return allocation


AD_USERS = {
    "alice": {"attributes": {"mail": "alice@example.edu"}},
    "bob": {"attributes": {"mail": ["bob@example.edu"]}},
}


def _get_user(wustlkey):
    if wustlkey not in AD_USERS:
        raise ValueError("Invalid wustlkey")
    return AD_USERS[wustlkey]


@patch(f"{MODULE}.ActiveDirectoryAPI")
class GetBillingContactEmailsTests(TestCase):
    def test_returns_unique_emails_in_allocation_order(self, mock_ad):
        mock_ad.return_value.get_user.side_effect = _get_user
        allocations = [
            _allocation(1, "bob"),
            _allocation(2, "alice"),
            _allocation(3, "bob"),
        ]

        self.assertEqual(
            get_billing_contact_emails(allocations),
            ["bob@example.edu", "alice@example.edu"],
        )

    def test_skips_missing_and_unknown_billing_contacts(self, mock_ad):
        mock_ad.return_value.get_user.side_effect = _get_user
        allocations = [
            _allocation(1, None),
            _allocation(2, "nobody"),
            _allocation(3, "alice"),
        ]

        self.assertEqual(get_billing_contact_emails(allocations), ["alice@example.edu"])


@patch(f"{MODULE}.send_mail")
@patch(f"{MODULE}.ActiveDirectoryAPI")
@patch(f"{MODULE}.StorageUsageReport")
class GenerateStorage3CondoUsageReportTests(TestCase):
    def test_sends_one_email_to_all_billing_contacts(
        self, mock_report_cls, mock_ad, mock_send_mail
    ):
        report = mock_report_cls.return_value
        report.generate_report_for_project.return_value = "REPORT"
        report.get_allocations_by_project.return_value = [
            _allocation(1, "alice"),
            _allocation(2, "bob"),
        ]
        mock_ad.return_value.get_user.side_effect = _get_user

        generate_storage3_condo_usage_report(
            usage_date="2026-11-01", project="Test Condo"
        )

        report.get_allocations_by_project.assert_called_once_with("Test Condo")
        mock_send_mail.assert_called_once()
        args = mock_send_mail.call_args.args
        self.assertEqual(args[3], ["alice@example.edu", "bob@example.edu"])
        self.assertIn("REPORT", args[1])

    def test_no_billing_contacts_sends_nothing(
        self, mock_report_cls, mock_ad, mock_send_mail
    ):
        report = mock_report_cls.return_value
        report.generate_report_for_project.return_value = "REPORT"
        report.get_allocations_by_project.return_value = [_allocation(1, None)]

        generate_storage3_condo_usage_report(
            usage_date="2026-11-01", project="Test Condo"
        )

        mock_send_mail.assert_not_called()

    @patch(f"{MODULE}.datetime")
    def test_default_usage_date_is_computed_at_call_time(
        self, mock_datetime, mock_report_cls, mock_ad, mock_send_mail
    ):
        report = mock_report_cls.return_value
        report.generate_report_for_project.return_value = "REPORT"
        report.get_allocations_by_project.return_value = []

        mock_datetime.now.return_value = datetime(2026, 11, 19, tzinfo=timezone.utc)
        generate_storage3_condo_usage_report(project="Test Condo")
        mock_datetime.now.return_value = datetime(2026, 12, 2, tzinfo=timezone.utc)
        generate_storage3_condo_usage_report(project="Test Condo")

        self.assertEqual(
            [c.kwargs["usage_date"] for c in mock_report_cls.call_args_list],
            ["2026-11-01", "2026-12-01"],
        )


class ScheduleCommandTests(TestCase):
    @patch(f"{MODULE}.schedule")
    def test_schedule_registers_on_call_failure_hook(self, mock_schedule):
        call_command(
            "add_scheduled_generate_storage3_condo_usage_report_monthly",
            "--project",
            "Test Condo",
        )

        mock_schedule.assert_called_once()
        self.assertEqual(
            mock_schedule.call_args.kwargs["hook"],
            "coldfront.plugins.qumulo.hooks.notify_on_call_on_failure_hook",
        )
