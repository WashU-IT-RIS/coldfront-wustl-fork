import json

from unittest.mock import MagicMock, call, patch

from django.test import Client, TestCase

from coldfront.core.allocation.models import AllocationAttribute, AllocationUser

from coldfront.plugins.qumulo.tests.utils.mock_data import build_models, create_allocation
from coldfront.plugins.qumulo.utils.acl_allocations import AclAllocations
from coldfront.plugins.qumulo.utils.workday_api import CURRENT_ATTESTATION_CYCLE_ID


@patch("coldfront.plugins.qumulo.views.allocation_users_api_view.ActiveDirectoryAPI")
class AllocationUsersApiViewTests(TestCase):
    def setUp(self):
        self.client = Client()

        build_data = build_models()
        self.project = build_data["project"]
        self.user = build_data["user"]

        self.client.force_login(self.user)

        self.form_data = {
            "storage_filesystem_path": "foo",
            "storage_export_path": "bar",
            "storage_ticket": "ITSD-54321",
            "storage_name": "baz",
            "storage_quota": 7,
            "protocols": ["nfs"],
            "rw_users": ["test", "shared-user"],
            "ro_users": ["other-user", "shared-user"],
            "cost_center": "Uncle Pennybags",
            "department_number": "Time Travel Services",
            "service_rate": "consumption",
        }

        self.storage_allocation = create_allocation(
            self.project, self.user, self.form_data
        )

        self.rw_allocation = AclAllocations.get_access_allocation(
            self.storage_allocation, "rw"
        )
        self.ro_allocation = AclAllocations.get_access_allocation(
            self.storage_allocation, "ro"
        )

    def test_post_adds_users_and_returns_storage_acl_name(
        self, mock_active_directory_api_cls: MagicMock
    ):
        mock_active_directory_api = mock_active_directory_api_cls.return_value

        response = self.client.post(
            f"/qumulo/allocation/{self.storage_allocation.pk}/access-users/",
            data=json.dumps(
                {"rw_users": ["new-rw-user"], "ro_users": ["new-ro-user"]}
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        response_payload = response.json()

        self.assertEqual(
            response_payload["storage_acl_name"]["rw"],
            self.rw_allocation.get_attribute("storage_acl_name"),
        )
        self.assertEqual(
            response_payload["storage_acl_name"]["ro"],
            self.ro_allocation.get_attribute("storage_acl_name"),
        )
        self.assertEqual(response_payload["added_users"]["rw"], ["new-rw-user"])
        self.assertEqual(response_payload["added_users"]["ro"], ["new-ro-user"])

        rw_usernames = list(
            AllocationUser.objects.filter(allocation=self.rw_allocation).values_list(
                "user__username", flat=True
            )
        )
        ro_usernames = list(
            AllocationUser.objects.filter(allocation=self.ro_allocation).values_list(
                "user__username", flat=True
            )
        )

        self.assertIn("new-rw-user", rw_usernames)
        self.assertIn("new-ro-user", ro_usernames)

        mock_active_directory_api.add_user_to_ad_group.assert_has_calls(
            [
                call(
                    wustlkey="new-rw-user",
                    group_name=self.rw_allocation.get_attribute("storage_acl_name"),
                ),
                call(
                    wustlkey="new-ro-user",
                    group_name=self.ro_allocation.get_attribute("storage_acl_name"),
                ),
            ],
            any_order=True,
        )

    def test_post_skips_users_already_on_allocation(
        self, mock_active_directory_api_cls: MagicMock
    ):
        mock_active_directory_api = mock_active_directory_api_cls.return_value

        response = self.client.post(
            f"/qumulo/allocation/{self.storage_allocation.pk}/access-users/",
            data=json.dumps({"rw_users": ["test"]}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        response_payload = response.json()

        self.assertEqual(response_payload["added_users"]["rw"], [])
        self.assertEqual(response_payload["added_users"]["ro"], [])
        mock_active_directory_api.add_user_to_ad_group.assert_not_called()

    def test_post_returns_400_for_invalid_payload(
        self, mock_active_directory_api_cls: MagicMock
    ):
        response = self.client.post(
            f"/qumulo/allocation/{self.storage_allocation.pk}/access-users/",
            data=json.dumps({"rw_users": "new-rw-user"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    def test_post_returns_400_when_no_users_provided(
        self, mock_active_directory_api_cls: MagicMock
    ):
        response = self.client.post(
            f"/qumulo/allocation/{self.storage_allocation.pk}/access-users/",
            data=json.dumps({}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    def test_delete_removes_users_and_returns_storage_acl_name(
        self, mock_active_directory_api_cls: MagicMock
    ):
        mock_active_directory_api = mock_active_directory_api_cls.return_value

        response = self.client.delete(
            f"/qumulo/allocation/{self.storage_allocation.pk}/access-users/",
            data=json.dumps({"users": ["shared-user"]}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        response_payload = response.json()

        self.assertEqual(
            response_payload["storage_acl_name"]["rw"],
            self.rw_allocation.get_attribute("storage_acl_name"),
        )
        self.assertEqual(
            response_payload["storage_acl_name"]["ro"],
            self.ro_allocation.get_attribute("storage_acl_name"),
        )
        self.assertEqual(response_payload["removed_users"]["rw"], ["shared-user"])
        self.assertEqual(response_payload["removed_users"]["ro"], ["shared-user"])

        rw_usernames = list(
            AllocationUser.objects.filter(allocation=self.rw_allocation).values_list(
                "user__username", flat=True
            )
        )
        ro_usernames = list(
            AllocationUser.objects.filter(allocation=self.ro_allocation).values_list(
                "user__username", flat=True
            )
        )

        self.assertNotIn("shared-user", rw_usernames)
        self.assertNotIn("shared-user", ro_usernames)


    def test_delete_returns_400_for_invalid_payload(
        self, mock_active_directory_api_cls: MagicMock
    ):
        response = self.client.delete(
            f"/qumulo/allocation/{self.storage_allocation.pk}/access-users/",
            data=json.dumps({"users": "shared-user"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    def test_delete_returns_empty_removed_users_when_user_not_found(
        self, mock_active_directory_api_cls: MagicMock
    ):
        mock_active_directory_api = mock_active_directory_api_cls.return_value

        response = self.client.delete(
            f"/qumulo/allocation/{self.storage_allocation.pk}/access-users/",
            data=json.dumps({"users": ["does-not-exist"]}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        response_payload = response.json()

        self.assertEqual(response_payload["removed_users"]["rw"], [])
        self.assertEqual(response_payload["removed_users"]["ro"], [])
        mock_active_directory_api.remove_member_from_group.assert_not_called()

    def test_post_ignores_attestation_when_gate_disabled(
        self, mock_active_directory_api_cls: MagicMock
    ):
        # ATTESTATION_GATE_ENABLED is unset in this test environment, so the
        # gate defaults to off and WorkdayAPI is never even instantiated.
        with patch(
            "coldfront.plugins.qumulo.views.allocation_users_api_view.WorkdayAPI"
        ) as mock_workday_api_cls:
            response = self.client.post(
                f"/qumulo/allocation/{self.storage_allocation.pk}/access-users/",
                data=json.dumps({"rw_users": ["new-rw-user"]}),
                content_type="application/json",
            )

        mock_workday_api_cls.assert_not_called()
        response_payload = response.json()
        self.assertEqual(response_payload["added_users"]["rw"], ["new-rw-user"])
        self.assertEqual(response_payload["pending_users"]["rw"], [])

    @patch("coldfront.plugins.qumulo.views.allocation_users_api_view.WorkdayAPI")
    def test_post_grants_access_when_gate_enabled_and_attestation_current(
        self, mock_workday_api_cls: MagicMock, mock_active_directory_api_cls: MagicMock
    ):
        mock_active_directory_api = mock_active_directory_api_cls.return_value
        mock_active_directory_api.find_wustlkey_by_universal_id.return_value = "new-rw-user"
        mock_workday_api_cls.return_value.get_completed_attestations.return_value = [
            {"universal_id": 12345, "attestation_cycle_id": "att_2026_q3", "due_date": "2026-09-01"}
        ]

        with patch.dict("os.environ", {"ATTESTATION_GATE_ENABLED": "true"}):
            response = self.client.post(
                f"/qumulo/allocation/{self.storage_allocation.pk}/access-users/",
                data=json.dumps({"rw_users": ["new-rw-user"]}),
                content_type="application/json",
            )

        response_payload = response.json()
        self.assertEqual(response_payload["added_users"]["rw"], ["new-rw-user"])
        self.assertEqual(response_payload["pending_users"]["rw"], [])
        self.assertTrue(
            AllocationUser.objects.filter(
                allocation=self.rw_allocation, user__username="new-rw-user"
            ).exists()
        )
        mock_active_directory_api.add_user_to_ad_group.assert_called_once_with(
            wustlkey="new-rw-user",
            group_name=self.rw_allocation.get_attribute("storage_acl_name"),
        )

    @patch("coldfront.plugins.qumulo.views.allocation_users_api_view.WorkdayAPI")
    def test_post_holds_user_pending_attestation_when_gate_enabled_and_not_completed(
        self, mock_workday_api_cls: MagicMock, mock_active_directory_api_cls: MagicMock
    ):
        mock_active_directory_api = mock_active_directory_api_cls.return_value
        mock_active_directory_api.find_wustlkey_by_universal_id.return_value = "someone-else"
        mock_workday_api_cls.return_value.get_completed_attestations.return_value = [
            {"universal_id": 12345, "attestation_cycle_id": "att_2026_q3", "due_date": "2026-09-01"}
        ]

        with patch.dict("os.environ", {"ATTESTATION_GATE_ENABLED": "true"}):
            response = self.client.post(
                f"/qumulo/allocation/{self.storage_allocation.pk}/access-users/",
                data=json.dumps({"rw_users": ["new-rw-user"]}),
                content_type="application/json",
            )

        response_payload = response.json()
        self.assertEqual(response_payload["added_users"]["rw"], [])
        self.assertEqual(response_payload["pending_users"]["rw"], ["new-rw-user"])

        self.assertFalse(
            AllocationUser.objects.filter(
                allocation=self.rw_allocation, user__username="new-rw-user"
            ).exists()
        )
        mock_active_directory_api.add_user_to_ad_group.assert_called_once_with(
            wustlkey="new-rw-user", group_name="ris-pre-onboard"
        )

        pending_attribute = AllocationAttribute.objects.get(
            allocation=self.rw_allocation, allocation_attribute_type__name="pending_attestation_event"
        )
        event = json.loads(pending_attribute.value)
        self.assertEqual(event["user_id"], "new-rw-user")
        self.assertEqual(event["attestation_cycle_id"], CURRENT_ATTESTATION_CYCLE_ID)
        self.assertEqual(
            event["revoked_entitlements"],
            [{"system": "coldfront", "allocation_id": self.storage_allocation.pk, "scope": "rw"}],
        )
