from django.test import TestCase, Client
from unittest.mock import MagicMock, patch, call

from coldfront_plugin_qumulo.tests.utils.mock_data import (
    build_models,
    create_allocation,
)
from coldfront_plugin_qumulo.utils.acl_allocations import AclAllocations, get_extra_aces
from coldfront_plugin_qumulo.utils.deafult_aces import default_aces

from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttribute,
    AllocationStatusChoice,
)
from ldap3.core.exceptions import LDAPException


class TestAclAllocations(TestCase):
    def setUp(self):
        self.client = Client()

        build_data = build_models()

        self.project = build_data["project"]
        self.user = build_data["user"]

        self.form_data = {
            "storage_filesystem_path": "foo",
            "storage_export_path": "bar",
            "storage_name": "baz",
            "storage_quota": 7,
            "protocols": ["nfs"],
            "rw_users": ["test"],
            "ro_users": [],
        }

        self.client.force_login(self.user)

    @patch("coldfront_plugin_qumulo.utils.acl_allocations.ActiveDirectoryAPI")
    @patch(
        "coldfront_plugin_qumulo.utils.acl_allocations.AclAllocations.create_acl_allocation"
    )
    def test_create_acl_allocations_calls_create_acl_allocation(
        self,
        mock_create_acl_allocation: MagicMock,
        mock_active_directory_api: MagicMock,
    ):
        mock_active_directory_instance = MagicMock()
        mock_active_directory_api.return_value = mock_active_directory_instance

        acl_allocations = AclAllocations(project_pk=self.project)
        ro_users, rw_users = ["ro_test"], ["rw_test"]
        acl_allocations.create_acl_allocations(ro_users=ro_users, rw_users=rw_users)

        self.assertEqual(mock_create_acl_allocation.call_count, 2)
        mock_create_acl_allocation.assert_any_call(
            acl_type="ro",
            users=ro_users,
            active_directory_api=mock_active_directory_instance,
        )
        mock_create_acl_allocation.assert_any_call(
            acl_type="rw",
            users=rw_users,
            active_directory_api=mock_active_directory_instance,
        )
        mock_active_directory_api.assert_called_once()

    @patch("coldfront_plugin_qumulo.utils.acl_allocations.ActiveDirectoryAPI")
    @patch(
        "coldfront_plugin_qumulo.utils.acl_allocations.AclAllocations.create_ad_group_and_add_users"
    )
    @patch(
        "coldfront_plugin_qumulo.utils.acl_allocations.AclAllocations.set_allocation_attributes"
    )
    @patch(
        "coldfront_plugin_qumulo.utils.acl_allocations.AclAllocations.add_allocation_users"
    )
    def test_create_acl_allocation_creates_acl_allocation(
        self,
        mock_add_allocation_users: MagicMock,
        mock_set_allocation_attributes: MagicMock,
        mock_create_ad_group_and_add_users: MagicMock,
        mock_active_directory_api: MagicMock,
    ):
        mock_add_allocation_users.return_value = MagicMock()
        mock_set_allocation_attributes.return_value = MagicMock()
        mock_create_ad_group_and_add_users.return_value = MagicMock()
        mock_active_directory_instance = MagicMock()
        mock_active_directory_api.return_value = mock_active_directory_instance

        acl_allocations = AclAllocations(project_pk=self.project)
        ro_users = ["ro_test"]
        acl_allocations.create_acl_allocation(
            acl_type="ro",
            users=ro_users,
            active_directory_api=mock_active_directory_instance,
        )

        all_allocation_objects = Allocation.objects.all()

        self.assertEqual(len(all_allocation_objects), 1)

        first_allocation = all_allocation_objects[0]
        self.assertEqual(first_allocation.project.id, 1)
        self.assertEqual(first_allocation.status.name, "Active")
        self.assertIsNotNone(first_allocation.resources.get(name="ro"))

        mock_add_allocation_users.assert_called_once_with(
            allocation=first_allocation, wustlkeys=ro_users
        )

        mock_set_allocation_attributes.assert_called_once_with(
            allocation=first_allocation, acl_type="ro", wustlkey="ro_test"
        )

        mock_create_ad_group_and_add_users.assert_called_once_with(
            wustlkeys=ro_users,
            allocation=first_allocation,
            active_directory_api=mock_active_directory_instance,
        )

    @patch("coldfront_plugin_qumulo.utils.acl_allocations.ActiveDirectoryAPI")
    @patch(
        "coldfront_plugin_qumulo.utils.acl_allocations.AclAllocations.create_ad_group_and_add_users",
        side_effect=LDAPException,
    )
    @patch(
        "coldfront_plugin_qumulo.utils.acl_allocations.AclAllocations.set_allocation_attributes"
    )
    @patch(
        "coldfront_plugin_qumulo.utils.acl_allocations.AclAllocations.add_allocation_users"
    )
    def test_create_acl_allocation_catches_LDAPexception_and_deletes_allocation(
        self,
        mock_add_allocation_users: MagicMock,
        mock_set_allocation_attributes: MagicMock,
        mock_create_ad_group_and_add_users: MagicMock,
        mock_active_directory_api: MagicMock,
    ):
        mock_add_allocation_users.return_value = MagicMock()
        mock_set_allocation_attributes.return_value = MagicMock()
        mock_active_directory_instance = MagicMock()
        mock_active_directory_api.return_value = mock_active_directory_instance

        acl_allocations = AclAllocations(project_pk=self.project)
        ro_users = ["ro_test"]

        acl_allocations.create_acl_allocation(
            acl_type="ro",
            users=ro_users,
            active_directory_api=mock_active_directory_instance,
        )

        self.assertEqual(len(Allocation.objects.all()), 0)

    def test_set_allocation_attributes_sets_allocation_attributes(self):
        test_allocation = Allocation.objects.create(
            project=self.project,
            justification="",
            quantity=1,
            status=AllocationStatusChoice.objects.get(name="Active"),
        )

        acl_allocations = AclAllocations(project_pk=self.project)
        acl_allocations.set_allocation_attributes(
            allocation=test_allocation, acl_type="ro", wustlkey="test"
        )

        all_allocation_attributes = AllocationAttribute.objects.all()

        self.assertEqual(len(all_allocation_attributes), 1)

    @patch("coldfront_plugin_qumulo.utils.acl_allocations.ActiveDirectoryAPI")
    def test_create_ad_group_and_add_users_creates_ad_group_and_adds_users(
        self, mock_active_directory_api
    ):
        mock_active_directory_instance = MagicMock()
        mock_active_directory_api.return_value = mock_active_directory_instance

        test_allocation = Allocation.objects.create(
            project=self.project,
            justification="",
            quantity=1,
            status=AllocationStatusChoice.objects.get(name="Active"),
        )

        AclAllocations.create_ad_group_and_add_users(
            wustlkeys=["ro_user"],
            allocation=test_allocation,
            active_directory_api=mock_active_directory_instance,
        )

        mock_active_directory_instance.add_user_to_ad_group.assert_called()

    @patch("coldfront_plugin_qumulo.utils.acl_allocations.ActiveDirectoryAPI")
    def test_create_ad_group_and_add_users_creates_ad_group_and_adds_users_without_ad_argument(
        self,
        mock_active_directory_api: MagicMock,
    ):
        mock_active_directory_instance = MagicMock()
        mock_active_directory_api.return_value = mock_active_directory_instance

        test_allocation = Allocation.objects.create(
            project=self.project,
            justification="",
            quantity=1,
            status=AllocationStatusChoice.objects.get(name="Active"),
        )

        AclAllocations.create_ad_group_and_add_users(
            wustlkeys=["ro_user"],
            allocation=test_allocation,
        )

        mock_active_directory_instance.add_user_to_ad_group.assert_called()

    def test_remove_access_sets_only_base_acls(self):
        test_allocation = create_allocation(self.project, self.user, self.form_data)
        acl_allocations = AclAllocations.get_access_allocations(test_allocation)

        calls = []

        mock_acl_data = {
            "control": ["PRESENT"],
            "posix_special_permissions": [],
            "aces": default_aces.copy(),
        }

        for acl_allocation in acl_allocations:
            calls.append(
                call(
                    acl=mock_acl_data,
                    path=test_allocation.get_attribute("storage_filesystem_path"),
                )
            )

        with patch(
            "coldfront_plugin_qumulo.utils.acl_allocations.QumuloAPI"
        ) as mock_qumulo_api:
            mock_return_data = {
                "control": ["PRESENT"],
                "posix_special_permissions": [],
                "aces": default_aces.copy(),
            }
            mock_return_data["aces"].extend(get_extra_aces(acl_allocations[0]))

            mock_qumulo_api.return_value.rc.fs.get_acl_v2.return_value = (
                mock_return_data
            )

            AclAllocations.remove_acl_access(allocation=test_allocation)

            mock_qumulo_api.return_value.rc.fs.set_acl_v2.assert_has_calls(calls)

    def test_remove_access_sets_allocation_status(self):
        test_allocation = create_allocation(self.project, self.user, self.form_data)
        acl_allocations = AclAllocations.get_access_allocations(test_allocation)

        with patch(
            "coldfront_plugin_qumulo.utils.acl_allocations.QumuloAPI"
        ) as mock_qumulo_api:
            mock_return_data = {
                "control": ["PRESENT"],
                "posix_special_permissions": [],
                "aces": default_aces.copy(),
            }
            mock_return_data["aces"].extend(get_extra_aces(acl_allocations[0]))

            mock_qumulo_api.return_value.rc.fs.get_acl_v2.return_value = (
                mock_return_data
            )

            AclAllocations.remove_acl_access(allocation=test_allocation)

            acl_allocations = AclAllocations.get_access_allocations(test_allocation)

            for acl_allocation in acl_allocations:
                self.assertEqual(acl_allocation.status.name, "Revoked")
