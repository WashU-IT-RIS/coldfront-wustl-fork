from datetime import datetime, timezone
from unittest import skipUnless
from unittest.mock import MagicMock, patch

import arrow
from django.conf import settings
from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings
from django_q.models import Schedule

from coldfront.plugins.qumulo.management.commands.add_scheduled_generate_storage3_condo_usage_report_monthly import (
    FAILURE_HOOK,
    REPORT_FUNC,
    REPORT_TIMEOUT_SECONDS,
    generate_storage3_condo_usage_report,
    get_billing_contact_emails,
    next_run_on_2nd_at_6_am_utc,
)
from coldfront.plugins.qumulo.reports.storage_usage_report import NO_USAGE_DATA

MODULE = "coldfront.plugins.qumulo.management.commands.add_scheduled_generate_storage3_condo_usage_report_monthly"

requires_email = skipUnless(
    getattr(settings, "EMAIL_ENABLED", False), "EMAIL_ENABLED is off"
)
COMMAND = "add_scheduled_generate_storage3_condo_usage_report_monthly"


def _allocation(pk, billing_contact):
    allocation = MagicMock()
    allocation.pk = pk
    allocation.get_attribute.side_effect = lambda name: (
        billing_contact if name == "billing_contact" else None
    )
    return allocation


def _usage(usage_kb):
    return {"usage_kb": usage_kb, "filesystem_path": "/path"}


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


@override_settings(DEBUG=False, DEFAULT_FROM_EMAIL="noreply@example.edu")
@patch(f"{MODULE}.send_mail")
@patch(f"{MODULE}.ActiveDirectoryAPI")
@patch(f"{MODULE}.StorageUsageReport")
class GenerateStorage3CondoUsageReportTests(TestCase):
    def _setup_report(self, mock_report_cls, mock_ad, usages=None, allocations=None):
        report = mock_report_cls.return_value
        report.generate_report_for_project.return_value = "REPORT"
        report.get_usages_for_project.return_value = (
            usages if usages is not None else [_usage("100.0")]
        )
        report.get_allocations_by_project.return_value = (
            allocations
            if allocations is not None
            else [_allocation(1, "alice"), _allocation(2, "bob")]
        )
        mock_ad.return_value.get_user.side_effect = _get_user
        return report

    @requires_email
    def test_sends_one_email_to_all_billing_contacts(
        self, mock_report_cls, mock_ad, mock_send_mail
    ):
        report = self._setup_report(mock_report_cls, mock_ad)

        generate_storage3_condo_usage_report(
            usage_date="2026-11-01", project="Test Condo"
        )

        report.get_allocations_by_project.assert_called_once_with("Test Condo")
        mock_send_mail.assert_called_once()
        args = mock_send_mail.call_args.args
        self.assertIn("REPORT", args[1])
        self.assertEqual(args[2], "noreply@example.edu")
        self.assertEqual(args[3], ["alice@example.edu", "bob@example.edu"])

    def test_no_billing_contacts_sends_nothing(
        self, mock_report_cls, mock_ad, mock_send_mail
    ):
        self._setup_report(mock_report_cls, mock_ad, allocations=[_allocation(1, None)])

        generate_storage3_condo_usage_report(
            usage_date="2026-11-01", project="Test Condo"
        )

        mock_send_mail.assert_not_called()

    @requires_email
    def test_some_allocations_without_usage_still_sends(
        self, mock_report_cls, mock_ad, mock_send_mail
    ):
        self._setup_report(
            mock_report_cls, mock_ad, usages=[_usage(NO_USAGE_DATA), _usage("5.0")]
        )

        generate_storage3_condo_usage_report(
            usage_date="2026-11-01", project="Test Condo"
        )

        mock_send_mail.assert_called_once()

    def test_no_usage_data_for_any_allocation_raises_and_sends_nothing(
        self, mock_report_cls, mock_ad, mock_send_mail
    ):
        self._setup_report(
            mock_report_cls,
            mock_ad,
            usages=[_usage(NO_USAGE_DATA), _usage(NO_USAGE_DATA)],
        )

        with self.assertRaisesRegex(ValueError, "No usage data recorded on 2026-11-01"):
            generate_storage3_condo_usage_report(
                usage_date="2026-11-01", project="Test Condo"
            )

        mock_send_mail.assert_not_called()

    def test_no_allocations_raises_and_sends_nothing(
        self, mock_report_cls, mock_ad, mock_send_mail
    ):
        self._setup_report(mock_report_cls, mock_ad, usages=[], allocations=[])

        with self.assertRaises(ValueError):
            generate_storage3_condo_usage_report(
                usage_date="2026-11-01", project="Test Condo"
            )

        mock_send_mail.assert_not_called()

    @requires_email
    def test_send_failure_raises(self, mock_report_cls, mock_ad, mock_send_mail):
        self._setup_report(mock_report_cls, mock_ad)
        mock_send_mail.side_effect = OSError("SMTP down")

        with self.assertRaises(OSError):
            generate_storage3_condo_usage_report(
                usage_date="2026-11-01", project="Test Condo"
            )

    @patch(f"{MODULE}.datetime")
    def test_default_usage_date_is_computed_at_call_time(
        self, mock_datetime, mock_report_cls, mock_ad, mock_send_mail
    ):
        self._setup_report(mock_report_cls, mock_ad)

        mock_datetime.now.return_value = datetime(2026, 11, 19, tzinfo=timezone.utc)
        generate_storage3_condo_usage_report(project="Test Condo")
        mock_datetime.now.return_value = datetime(2026, 12, 2, tzinfo=timezone.utc)
        generate_storage3_condo_usage_report(project="Test Condo")

        self.assertEqual(
            [c.kwargs["usage_date"] for c in mock_report_cls.call_args_list],
            ["2026-11-01", "2026-12-01"],
        )


class NextRunTests(TestCase):
    def test_before_the_2nd_runs_this_month(self):
        now = arrow.get("2026-11-01T23:00:00+00:00")
        self.assertEqual(arrow.get(next_run_on_2nd_at_6_am_utc(now)), arrow.get("2026-11-02T06:00:00+00:00"))

    def test_on_the_2nd_before_6_am_runs_today(self):
        now = arrow.get("2026-11-02T05:59:00+00:00")
        self.assertEqual(arrow.get(next_run_on_2nd_at_6_am_utc(now)), arrow.get("2026-11-02T06:00:00+00:00"))

    def test_after_the_2nd_runs_next_month(self):
        now = arrow.get("2026-11-19T12:34:56.789+00:00")
        self.assertEqual(arrow.get(next_run_on_2nd_at_6_am_utc(now)), arrow.get("2026-12-02T06:00:00+00:00"))

    def test_december_rolls_into_january(self):
        now = arrow.get("2026-12-15T00:00:00+00:00")
        self.assertEqual(arrow.get(next_run_on_2nd_at_6_am_utc(now)), arrow.get("2027-01-02T06:00:00+00:00"))
