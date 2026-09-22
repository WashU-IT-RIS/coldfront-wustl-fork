from io import StringIO
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.test import TestCase

from coldfront.core.allocation.models import AllocationAttribute, AllocationUser

from coldfront.plugins.qumulo.tests.utils.mock_data import build_models, create_allocation
from coldfront.plugins.qumulo.utils.acl_allocations import AclAllocations
from coldfront.plugins.qumulo.utils.attestation import record_pending_attestation_event


COMMAND = "restore_pending_attestation_access"
MODULE = "coldfront.plugins.qumulo.management.commands.restore_pending_attestation_access"


def _overdue_record(**overrides):
    record = {"universal_id": 12345, "attestation_cycle_id": "att_2026_q3", "due_date": "2026-09-01"}
    record.update(overrides)
    return record


@patch(f"{MODULE}.WorkdayAPI")
@patch(f"{MODULE}.ActiveDirectoryAPI")
class TestRestorePendingAttestationAccess(TestCase):
    def setUp(self):
        build_data = build_models()
        self.project = build_data["project"]
        self.user = build_data["user"]

        self.form_data = {
            "storage_filesystem_path": "foo",
            "storage_export_path": "bar",
            "storage_ticket": "ITSD-54321",
            "storage_name": "baz",
            "storage_quota": 7,
            "protocols": ["nfs"],
            "rw_users": ["test"],
            "ro_users": [],
            "cost_center": "Uncle Pennybags",
            "department_number": "Time Travel Services",
            "service_rate": "consumption",
        }
        self.storage_allocation = create_allocation(self.project, self.user, self.form_data)
        self.rw_allocation = AclAllocations.get_access_allocation(self.storage_allocation, "rw")
        self.event = record_pending_attestation_event(self.rw_allocation, "held-user", "rw", "att_2026_q3")

    def test_restores_access_when_now_attested(self, mock_ad_api_cls, mock_workday_api_cls):
        mock_ad_api = mock_ad_api_cls.return_value
        mock_ad_api.find_wustlkey_by_universal_id.return_value = "someone-else"
        mock_workday_api_cls.return_value.get_overdue_attestations.return_value = [_overdue_record()]

        out = StringIO()
        call_command(COMMAND, stdout=out)

        self.assertTrue(
            AllocationUser.objects.filter(allocation=self.rw_allocation, user__username="held-user").exists()
        )
        mock_ad_api.add_user_to_ad_group.assert_called_once_with(
            wustlkey="held-user", group_name=self.rw_allocation.get_attribute("storage_acl_name")
        )
        mock_ad_api.remove_member_from_group.assert_called_once_with("held-user", "ris-pre-onboard")
        self.assertFalse(
            AllocationAttribute.objects.filter(
                allocation=self.rw_allocation, allocation_attribute_type__name="pending_attestation_event"
            ).exists()
        )
        self.assertIn("held-user", out.getvalue())
        self.assertIn("restored access", out.getvalue())

    def test_leaves_user_held_when_still_overdue(self, mock_ad_api_cls, mock_workday_api_cls):
        mock_ad_api = mock_ad_api_cls.return_value
        mock_ad_api.find_wustlkey_by_universal_id.return_value = "held-user"
        mock_workday_api_cls.return_value.get_overdue_attestations.return_value = [_overdue_record()]

        out = StringIO()
        call_command(COMMAND, stdout=out)

        self.assertFalse(
            AllocationUser.objects.filter(allocation=self.rw_allocation, user__username="held-user").exists()
        )
        mock_ad_api.add_user_to_ad_group.assert_not_called()
        mock_ad_api.remove_member_from_group.assert_not_called()
        self.assertTrue(
            AllocationAttribute.objects.filter(
                allocation=self.rw_allocation, allocation_attribute_type__name="pending_attestation_event"
            ).exists()
        )
        self.assertIn("still overdue", out.getvalue())

    def test_dry_run_does_not_mutate_anything(self, mock_ad_api_cls, mock_workday_api_cls):
        mock_ad_api = mock_ad_api_cls.return_value
        mock_ad_api.find_wustlkey_by_universal_id.return_value = "someone-else"
        mock_workday_api_cls.return_value.get_overdue_attestations.return_value = [_overdue_record()]

        out = StringIO()
        call_command(COMMAND, "--dry-run", stdout=out)

        self.assertFalse(
            AllocationUser.objects.filter(allocation=self.rw_allocation, user__username="held-user").exists()
        )
        mock_ad_api.add_user_to_ad_group.assert_not_called()
        mock_ad_api.remove_member_from_group.assert_not_called()
        self.assertTrue(
            AllocationAttribute.objects.filter(
                allocation=self.rw_allocation, allocation_attribute_type__name="pending_attestation_event"
            ).exists()
        )
        self.assertIn("would restore", out.getvalue())

    def test_reports_when_nothing_pending(self, mock_ad_api_cls, mock_workday_api_cls):
        AllocationAttribute.objects.filter(allocation_attribute_type__name="pending_attestation_event").delete()

        out = StringIO()
        call_command(COMMAND, stdout=out)

        mock_workday_api_cls.return_value.get_overdue_attestations.assert_not_called()
        self.assertIn("No pending attestation events found.", out.getvalue())
