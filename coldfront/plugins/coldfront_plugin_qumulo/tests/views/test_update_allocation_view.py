from django.test import TestCase, Client
from unittest.mock import patch, call, MagicMock

from coldfront.core.allocation.models import AllocationUser

from coldfront_plugin_qumulo.views.update_allocation_view import UpdateAllocationView
from coldfront_plugin_qumulo.tests.utils.mock_data import (
    create_allocation,
    build_models,
)
from coldfront_plugin_qumulo.utils.acl_allocations import AclAllocations


@patch("coldfront_plugin_qumulo.views.update_allocation_view.ActiveDirectoryAPI")
class UpdateAllocationViewTests(TestCase):
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
            "rw_users": ["test"],
            "ro_users": [],
            "cost_center": "Uncle Pennybags",
            "department_number": "Time Travel Services",
            "service_rate": "consumption",
        }

        self.storage_allocation = create_allocation(
            self.project, self.user, self.form_data
        )

    def test_get_access_users_returns_one_user(
        self, mock_ActiveDirectoryAPI: MagicMock
    ):
        form_data = {
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

        storage_allocation = create_allocation(self.project, self.user, form_data)

        access_users = UpdateAllocationView.get_access_users("rw", storage_allocation)

        self.assertCountEqual(access_users, form_data["rw_users"])

    def test_get_access_users_returns_multiple_users(
        self, mock_ActiveDirectoryAPI: MagicMock
    ):
        form_data = {
            "storage_filesystem_path": "foo",
            "storage_export_path": "bar",
            "storage_ticket": "ITSD-54321",
            "storage_name": "baz",
            "storage_quota": 7,
            "protocols": ["nfs"],
            "rw_users": ["test", "foo", "bar"],
            "ro_users": [],
            "cost_center": "Uncle Pennybags",
            "department_number": "Time Travel Services",
            "service_rate": "consumption",
        }

        storage_allocation = create_allocation(self.project, self.user, form_data)

        access_users = UpdateAllocationView.get_access_users("rw", storage_allocation)

        self.assertCountEqual(access_users, form_data["rw_users"])

    def test_get_access_users_returns_no_users(
        self, mock_ActiveDirectoryAPI: MagicMock
    ):
        form_data = {
            "storage_filesystem_path": "foo",
            "storage_export_path": "bar",
            "storage_ticket": "ITSD-54321",
            "storage_name": "baz",
            "storage_quota": 7,
            "protocols": ["nfs"],
            "rw_users": ["test", "foo", "bar"],
            "ro_users": [],
            "cost_center": "Uncle Pennybags",
            "department_number": "Time Travel Services",
            "service_rate": "consumption",
        }

        storage_allocation = create_allocation(self.project, self.user, form_data)

        access_users = UpdateAllocationView.get_access_users("ro", storage_allocation)

        self.assertCountEqual(access_users, form_data["ro_users"])

    def test_set_access_users_ignores_unchanged(
        self, mock_ActiveDirectoryAPI: MagicMock
    ):

        form_data = {
            "storage_filesystem_path": "foo",
            "storage_export_path": "bar",
            "storage_ticket": "ITSD-54321",
            "storage_name": "baz",
            "storage_quota": 7,
            "protocols": ["nfs"],
            "rw_users": ["test", "foo", "bar"],
            "ro_users": [],
            "cost_center": "Uncle Pennybags",
            "department_number": "Time Travel Services",
            "service_rate": "consumption",
        }

        storage_allocation = create_allocation(self.project, self.user, form_data)

        with patch(
            "coldfront_plugin_qumulo.views.update_allocation_view.AclAllocations.add_user_to_access_allocation",
        ) as mock_add_user_to_access_allocation:
            UpdateAllocationView.set_access_users(
                "rw", form_data["rw_users"], storage_allocation
            )

            mock_add_user_to_access_allocation.assert_not_called()

    def test_set_access_users_adds_new_user(self, mock_ActiveDirectoryAPI: MagicMock):
        form_data = {
            "storage_filesystem_path": "foo",
            "storage_export_path": "bar",
            "storage_ticket": "ITSD-54321",
            "storage_name": "baz",
            "storage_quota": 7,
            "protocols": ["nfs"],
            "rw_users": ["test", "foo", "bar"],
            "ro_users": [],
            "cost_center": "Uncle Pennybags",
            "department_number": "Time Travel Services",
            "service_rate": "consumption",
        }

        storage_allocation = create_allocation(self.project, self.user, form_data)

        new_rw_users: list = form_data["rw_users"].copy()
        new_rw_users.append("baz")

        with patch(
            "coldfront_plugin_qumulo.views.update_allocation_view.AclAllocations.add_user_to_access_allocation",
        ) as mock_add_user_to_access_allocation:
            UpdateAllocationView.set_access_users(
                "rw", new_rw_users, storage_allocation
            )

            access_allocation = AclAllocations.get_access_allocation(
                storage_allocation, "rw"
            )

            mock_add_user_to_access_allocation.assert_called_once_with(
                "baz", access_allocation
            )

    def test_set_access_users_adds_new_users(self, mock_ActiveDirectoryAPI: MagicMock):
        form_data = {
            "storage_filesystem_path": "foo",
            "storage_export_path": "bar",
            "storage_ticket": "ITSD-54321",
            "storage_name": "baz",
            "storage_quota": 7,
            "protocols": ["nfs"],
            "rw_users": ["test", "foo", "bar"],
            "ro_users": [],
            "cost_center": "Uncle Pennybags",
            "department_number": "Time Travel Services",
            "service_rate": "consumption",
        }

        with patch(
            "coldfront_plugin_qumulo.signals.update_user_with_additional_data"
        ) as mock_update:
            storage_allocation = create_allocation(self.project, self.user, form_data)
            update_calls = [
                call("foo"),
                call("bar"),
            ]
            mock_update.assert_has_calls(update_calls)
            assert mock_update.call_count == 2

        extra_users = ["baz", "bah"]
        new_rw_users: list = form_data["rw_users"].copy() + extra_users

        with patch(
            "coldfront_plugin_qumulo.views.update_allocation_view.AclAllocations.add_user_to_access_allocation",
        ) as mock_add_user_to_access_allocation:
            UpdateAllocationView.set_access_users(
                "rw", new_rw_users, storage_allocation
            )

            access_allocation = AclAllocations.get_access_allocation(
                storage_allocation, "rw"
            )

            calls = []
            for user in extra_users:
                calls.append(call(user, access_allocation))

            mock_add_user_to_access_allocation.assert_has_calls(calls)

    def test_set_access_users_removes_user(self, mock_ActiveDirectoryAPI: MagicMock):
        form_data = {
            "storage_filesystem_path": "foo",
            "storage_export_path": "bar",
            "storage_ticket": "ITSD-54321",
            "storage_name": "baz",
            "storage_quota": 7,
            "protocols": ["nfs"],
            "rw_users": ["test", "foo", "bar"],
            "ro_users": [],
            "cost_center": "Uncle Pennybags",
            "department_number": "Time Travel Services",
            "service_rate": "consumption",
        }

        storage_allocation = create_allocation(self.project, self.user, form_data)

        new_rw_users: list = form_data["rw_users"].copy()
        new_rw_users.remove("test")

        UpdateAllocationView.set_access_users("rw", new_rw_users, storage_allocation)

        access_allocation = AclAllocations.get_access_allocation(
            storage_allocation, "rw"
        )
        access_allocation_users = AllocationUser.objects.filter(
            allocation=access_allocation
        )
        access_usernames = [
            allocation_user.user.username for allocation_user in access_allocation_users
        ]

        self.assertNotIn("test", access_usernames)

    def test_set_access_users_adds_user_to_ad(self, mock_ActiveDirectoryAPI: MagicMock):
        mock_active_directory_api = mock_ActiveDirectoryAPI.return_value

        form_data = {
            "storage_filesystem_path": "foo",
            "storage_export_path": "bar",
            "storage_ticket": "ITSD-54321",
            "storage_name": "baz",
            "storage_quota": 7,
            "protocols": ["nfs"],
            "rw_users": ["test", "foo", "bar"],
            "ro_users": [],
            "cost_center": "Uncle Pennybags",
            "department_number": "Time Travel Services",
            "service_rate": "consumption",
        }

        storage_allocation = create_allocation(self.project, self.user, form_data)

        new_rw_users: list = form_data["rw_users"].copy()
        new_rw_users.append("baz")

        UpdateAllocationView.set_access_users("rw", new_rw_users, storage_allocation)

        access_allocation = AclAllocations.get_access_allocation(
            storage_allocation, "rw"
        )

        mock_active_directory_api.add_user_to_ad_group.assert_called_once_with(
            "baz", access_allocation.get_attribute("storage_acl_name")
        )

    def test_set_access_users_removes_user(self, mock_ActiveDirectoryAPI: MagicMock):
        mock_active_directory_api = mock_ActiveDirectoryAPI.return_value

        form_data = {
            "storage_filesystem_path": "foo",
            "storage_export_path": "bar",
            "storage_ticket": "ITSD-54321",
            "storage_name": "baz",
            "storage_quota": 7,
            "protocols": ["nfs"],
            "rw_users": ["test", "foo", "bar"],
            "ro_users": [],
            "cost_center": "Uncle Pennybags",
            "department_number": "Time Travel Services",
            "service_rate": "consumption",
        }

        storage_allocation = create_allocation(self.project, self.user, form_data)

        new_rw_users: list = form_data["rw_users"].copy()
        new_rw_users.remove("test")

        UpdateAllocationView.set_access_users("rw", new_rw_users, storage_allocation)

        access_allocation = AclAllocations.get_access_allocation(
            storage_allocation, "rw"
        )

        mock_active_directory_api.remove_user_from_group.assert_called_once_with(
            "test", access_allocation.get_attribute("storage_acl_name")
        )
