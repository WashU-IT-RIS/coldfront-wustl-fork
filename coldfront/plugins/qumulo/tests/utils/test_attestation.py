import json
import os
from unittest.mock import MagicMock, patch

from django.test import TestCase

from coldfront.core.allocation.models import AllocationAttribute, AllocationAttributeType

from coldfront.plugins.qumulo.tests.utils.mock_data import build_models, create_allocation
from coldfront.plugins.qumulo.utils.acl_allocations import AclAllocations
from coldfront.plugins.qumulo.utils.attestation import (
    attestation_gate_enabled,
    build_pending_attestation_event,
    find_overdue_attestation,
    get_pending_attestation_events,
    pre_onboard_group_name,
    record_pending_attestation_event,
)


def _overdue_record(**overrides):
    record = {"universal_id": 12345, "attestation_cycle_id": "att_2026_q3", "due_date": "2026-09-01"}
    record.update(overrides)
    return record


class TestAttestationGateConfig(TestCase):
    def test_pre_onboard_group_name_defaults(self):
        with patch.dict("os.environ", {}, clear=False):
            os.environ.pop("AD_PRE_ONBOARD_GROUP", None)
            self.assertEqual(pre_onboard_group_name(), "ris-pre-onboard")

    def test_pre_onboard_group_name_reads_env_override(self):
        with patch.dict("os.environ", {"AD_PRE_ONBOARD_GROUP": "custom-pre-onboard"}):
            self.assertEqual(pre_onboard_group_name(), "custom-pre-onboard")

    def test_attestation_gate_enabled_defaults_to_false(self):
        with patch.dict("os.environ", {}, clear=False):
            os.environ.pop("ATTESTATION_GATE_ENABLED", None)
            self.assertFalse(attestation_gate_enabled())

    def test_attestation_gate_enabled_reads_truthy_values(self):
        for value in ["1", "true", "True", "yes"]:
            with patch.dict("os.environ", {"ATTESTATION_GATE_ENABLED": value}):
                self.assertTrue(attestation_gate_enabled(), f"expected {value!r} to enable the gate")

    def test_attestation_gate_enabled_treats_other_values_as_false(self):
        with patch.dict("os.environ", {"ATTESTATION_GATE_ENABLED": "false"}):
            self.assertFalse(attestation_gate_enabled())


class TestFindOverdueAttestation(TestCase):
    def test_matches_resolved_wustlkey(self):
        mock_ad_api = MagicMock()
        mock_ad_api.find_wustlkey_by_universal_id.return_value = "sleong"

        record = find_overdue_attestation("sleong", mock_ad_api, [_overdue_record()])

        mock_ad_api.find_wustlkey_by_universal_id.assert_called_once_with(12345)
        self.assertEqual(record, _overdue_record())

    def test_returns_none_when_user_not_in_overdue_list(self):
        mock_ad_api = MagicMock()
        mock_ad_api.find_wustlkey_by_universal_id.return_value = "someone-else"

        self.assertIsNone(find_overdue_attestation("sleong", mock_ad_api, [_overdue_record()]))

    def test_returns_none_for_empty_overdue_list(self):
        mock_ad_api = MagicMock()
        self.assertIsNone(find_overdue_attestation("sleong", mock_ad_api, []))

    def test_skips_unresolvable_records(self):
        records = [_overdue_record(universal_id=11111), _overdue_record(universal_id=22222)]

        def fake_resolve(universal_id):
            if universal_id == 11111:
                raise ValueError("no AD user found")
            return "sleong"

        mock_ad_api = MagicMock()
        mock_ad_api.find_wustlkey_by_universal_id.side_effect = fake_resolve

        record = find_overdue_attestation("sleong", mock_ad_api, records)

        self.assertEqual(record, records[1])


class TestBuildPendingAttestationEvent(TestCase):
    def test_event_shape(self):
        event = build_pending_attestation_event("sleong", 18, "rw", "att_2026_q3")

        self.assertTrue(event["event_id"].startswith("evt_"))
        self.assertTrue(event["timestamp"].endswith("Z"))
        self.assertEqual(event["action"], "ACCESS_REVOKED_PENDING_ATTESTATION")
        self.assertEqual(event["user_id"], "sleong")
        self.assertEqual(
            event["revoked_entitlements"], [{"system": "coldfront", "allocation_id": 18, "scope": "rw"}]
        )
        self.assertEqual(event["attestation_cycle_id"], "att_2026_q3")
        self.assertTrue(event["restoration_token"].startswith("sleong_"))
        self.assertIsNone(event["source_event_id"])

    def test_attestation_cycle_id_defaults_to_none(self):
        event = build_pending_attestation_event("sleong", 18, "rw")
        self.assertIsNone(event["attestation_cycle_id"])


class TestPendingAttestationEventPersistence(TestCase):
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

    def test_record_pending_attestation_event_creates_attribute_on_access_allocation(self):
        event = record_pending_attestation_event(self.rw_allocation, "new-user", "rw", "att_2026_q3")

        attribute = AllocationAttribute.objects.get(
            allocation=self.rw_allocation, allocation_attribute_type__name="pending_attestation_event"
        )
        self.assertEqual(json.loads(attribute.value), event)
        self.assertEqual(event["user_id"], "new-user")
        self.assertEqual(
            event["revoked_entitlements"],
            [{"system": "coldfront", "allocation_id": self.storage_allocation.pk, "scope": "rw"}],
        )

    def test_get_pending_attestation_events_returns_all_pending_events(self):
        record_pending_attestation_event(self.rw_allocation, "user-a", "rw", "att_2026_q3")
        record_pending_attestation_event(self.rw_allocation, "user-b", "rw", "att_2026_q3")

        events = get_pending_attestation_events()

        usernames = {event["user_id"] for _, event in events}
        self.assertEqual(usernames, {"user-a", "user-b"})

    def test_get_pending_attestation_events_returns_empty_when_none_pending(self):
        self.assertEqual(get_pending_attestation_events(), [])

    def test_get_pending_attestation_events_skips_malformed_values(self):
        AllocationAttribute.objects.create(
            allocation_attribute_type=AllocationAttributeType.objects.get(name="pending_attestation_event"),
            allocation=self.rw_allocation,
            value="not-json",
        )

        self.assertEqual(get_pending_attestation_events(), [])
