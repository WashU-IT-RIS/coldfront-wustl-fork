import json

from django.test import Client, TestCase

from coldfront.core.allocation.models import  AllocationUser

from coldfront.plugins.qumulo.tests.utils.mock_data import (
    build_models,
    create_allocation,
)
from coldfront.plugins.qumulo.utils.acl_allocations import AclAllocations


class AllocationUsersApiTests(TestCase):
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
        self,
    ):

        response = self.client.post(
            f"/qumulo/allocation/{self.storage_allocation.pk}/access-users/",
            data=json.dumps({"rw_users": ["new-rw-user"], "ro_users": ["new-ro-user"]}),
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

    def test_post_skips_users_already_on_allocation(
        self,
    ):

        response = self.client.post(
            f"/qumulo/allocation/{self.storage_allocation.pk}/access-users/",
            data=json.dumps({"rw_users": ["test"]}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        response_payload = response.json()

        self.assertEqual(response_payload["added_users"]["rw"], [])
        self.assertEqual(response_payload["added_users"]["ro"], [])

    def test_post_returns_400_for_invalid_payload(
        self,
    ):
        response = self.client.post(
            f"/qumulo/allocation/{self.storage_allocation.pk}/access-users/",
            data=json.dumps({"rw_users": "new-rw-user"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    def test_post_returns_400_when_no_users_provided(
        self,
    ):
        response = self.client.post(
            f"/qumulo/allocation/{self.storage_allocation.pk}/access-users/",
            data=json.dumps({}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    def test_delete_removes_users_and_returns_storage_acl_name(
        self,
    ):

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
        self,
    ):
        response = self.client.delete(
            f"/qumulo/allocation/{self.storage_allocation.pk}/access-users/",
            data=json.dumps({"users": "shared-user"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    def test_delete_returns_empty_removed_users_when_user_not_found(
        self,
    ):

        response = self.client.delete(
            f"/qumulo/allocation/{self.storage_allocation.pk}/access-users/",
            data=json.dumps({"users": ["does-not-exist"]}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        response_payload = response.json()

        self.assertEqual(response_payload["removed_users"]["rw"], [])
        self.assertEqual(response_payload["removed_users"]["ro"], [])
