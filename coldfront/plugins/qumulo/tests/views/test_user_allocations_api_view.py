from django.contrib.auth.models import User
from django.test import Client, TestCase

from coldfront.plugins.qumulo.tests.utils.mock_data import build_models, create_allocation


class UserAllocationsApiViewTests(TestCase):
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

    def test_get_returns_allocation_with_both_rw_and_ro_access(self):
        response = self.client.get("/qumulo/allocation/users/shared-user/")

        self.assertEqual(response.status_code, 200)
        response_payload = response.json()

        self.assertEqual(response_payload["username"], "shared-user")
        self.assertEqual(len(response_payload["allocations"]), 1)

        allocation_payload = response_payload["allocations"][0]
        self.assertEqual(allocation_payload["allocation_id"], self.storage_allocation.pk)
        self.assertEqual(allocation_payload["project_id"], self.project.pk)
        self.assertEqual(allocation_payload["project_name"], self.project.title)
        self.assertEqual(allocation_payload["storage_name"], "baz")
        self.assertEqual(allocation_payload["access"], ["ro", "rw"])

    def test_get_returns_allocation_with_only_rw_access(self):
        response = self.client.get("/qumulo/allocation/users/test/")

        self.assertEqual(response.status_code, 200)
        response_payload = response.json()

        self.assertEqual(len(response_payload["allocations"]), 1)
        self.assertEqual(response_payload["allocations"][0]["access"], ["rw"])

    def test_get_returns_empty_allocations_for_user_with_no_access(self):
        User.objects.create(username="no-access-user")

        response = self.client.get("/qumulo/allocation/users/no-access-user/")

        self.assertEqual(response.status_code, 200)
        response_payload = response.json()

        self.assertEqual(response_payload["username"], "no-access-user")
        self.assertEqual(response_payload["allocations"], [])

    def test_get_returns_404_for_unknown_username(self):
        response = self.client.get("/qumulo/allocation/users/does-not-exist/")

        self.assertEqual(response.status_code, 404)
