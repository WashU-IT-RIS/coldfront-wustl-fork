from django.test import Client, TestCase, RequestFactory
from django.contrib import messages
from unittest.mock import patch, MagicMock
import json

from coldfront.core.allocation.models import AllocationUser

from coldfront.plugins.qumulo.forms.UpdateAllocationForm import UpdateAllocationForm
from coldfront.plugins.qumulo.hooks import acl_reset_complete_hook
from coldfront.plugins.qumulo.tasks import addMembersToADGroup, reset_allocation_acls
from coldfront.plugins.qumulo.views.update_allocation_view import UpdateAllocationView
from coldfront.plugins.qumulo.tests.utils.mock_data import (
    create_allocation,
    build_models,
)
from coldfront.plugins.qumulo.utils.acl_allocations import AclAllocations

from coldfront.core.allocation.models import (
    AllocationAttributeChangeRequest,
)


@patch("coldfront.plugins.qumulo.views.allocation_view.FileSystemService")
@patch("coldfront.plugins.qumulo.views.update_allocation_view.async_task")
@patch("coldfront.plugins.qumulo.views.update_allocation_view.ActiveDirectoryAPI")
class UpdateAllocationViewTests(TestCase):
    def setUp(self):
        self.client = Client()

        build_data = build_models()

        self.project = build_data["project"]
        self.user = build_data["user"]

        self.client.force_login(self.user)

        self.request = RequestFactory().get("/request/path/does/not/matter/")
        self.request.user = self.user

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
            "billing_exempt": "No",
            "department_number": "Time Travel Services",
            "billing_cycle": "monthly",
            "service_rate": "consumption",
            "technical_contact": "it.guru",
            "billing_contact": "finance.guru",
        }

        self.storage_allocation = create_allocation(
            self.project, self.user, self.form_data
        )

    def test_get_access_users_returns_one_user(
        self,
        mock_ActiveDirectoryAPI: MagicMock,
        mock_async_task: MagicMock,
        mock_file_system_service: MagicMock,
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
            "billing_exempt": "No",
            "department_number": "Time Travel Services",
            "billing_cycle": "monthly",
            "service_rate": "consumption",
        }

        storage_allocation = create_allocation(self.project, self.user, form_data)

        access_users = UpdateAllocationView.get_access_users("rw", storage_allocation)

        self.assertCountEqual(access_users, form_data["rw_users"])

    def test_get_access_users_returns_multiple_users(
        self,
        mock_ActiveDirectoryAPI: MagicMock,
        mock_async_task: MagicMock,
        mock_file_system_service: MagicMock,
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
            "billing_exempt": "No",
            "department_number": "Time Travel Services",
            "billing_cycle": "monthly",
            "service_rate": "consumption",
        }

        storage_allocation = create_allocation(self.project, self.user, form_data)

        access_users = UpdateAllocationView.get_access_users("rw", storage_allocation)

        self.assertCountEqual(access_users, form_data["rw_users"])

    def test_get_access_users_returns_no_users(
        self,
        mock_ActiveDirectoryAPI: MagicMock,
        mock_async_task: MagicMock,
        mock_file_system_service: MagicMock,
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
            "billing_exempt": "No",
            "department_number": "Time Travel Services",
            "billing_cycle": "monthly",
            "service_rate": "consumption",
        }

        storage_allocation = create_allocation(self.project, self.user, form_data)

        access_users = UpdateAllocationView.get_access_users("ro", storage_allocation)

        self.assertCountEqual(access_users, form_data["ro_users"])

    def test_set_access_users_ignores_unchanged(
        self,
        mock_ActiveDirectoryAPI: MagicMock,
        mock_async_task: MagicMock,
        mock_file_system_service: MagicMock,
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
            "billing_exempt": "No",
            "department_number": "Time Travel Services",
            "billing_cycle": "monthly",
            "service_rate": "consumption",
        }

        storage_allocation = create_allocation(self.project, self.user, form_data)

        with patch(
            "coldfront.plugins.qumulo.views.update_allocation_view.AclAllocations.add_user_to_access_allocation",
        ) as mock_add_user_to_access_allocation:
            UpdateAllocationView.set_access_users(
                "rw", form_data["rw_users"], storage_allocation
            )

            mock_add_user_to_access_allocation.assert_not_called()

    def test_set_access_users_removes_user(
        self,
        mock_ActiveDirectoryAPI: MagicMock,
        mock_async_task: MagicMock,
        mock_file_system_service: MagicMock,
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
            "billing_exempt": "No",
            "department_number": "Time Travel Services",
            "billing_cycle": "monthly",
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

    def test_set_access_users_removes_user_ad(
        self,
        mock_ActiveDirectoryAPI: MagicMock,
        mock_async_task: MagicMock,
        mock_file_system_service: MagicMock,
    ):
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
            "billing_exempt": "No",
            "department_number": "Time Travel Services",
            "billing_cycle": "monthly",
            "service_rate": "consumption",
        }

        storage_allocation = create_allocation(self.project, self.user, form_data)

        new_rw_users: list = form_data["rw_users"].copy()
        new_rw_users.remove("test")

        UpdateAllocationView.set_access_users("rw", new_rw_users, storage_allocation)

        access_allocation = AclAllocations.get_access_allocation(
            storage_allocation, "rw"
        )

        mock_active_directory_api.remove_member_from_group.assert_called_once_with(
            "test", access_allocation.get_attribute("storage_acl_name")
        )

    def test_set_access_users_adds_user(
        self,
        mock_ActiveDirectoryAPI: MagicMock,
        mock_async_task: MagicMock,
        mock_file_system_service: MagicMock,
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
            "billing_exempt": "No",
            "department_number": "Time Travel Services",
            "billing_cycle": "monthly",
            "service_rate": "consumption",
        }
        storage_allocation = create_allocation(self.project, self.user, form_data)

        new_rw_users: list = form_data["rw_users"].copy()
        new_rw_users.append("newuser")

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

        self.assertIn("test", access_usernames)

    def test_set_access_users_adds_user_ad(
        self,
        mock_ActiveDirectoryAPI: MagicMock,
        mock_async_task: MagicMock,
        mock_file_system_service: MagicMock,
    ):
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
            "billing_exempt": "No",
            "department_number": "Time Travel Services",
            "billing_cycle": "monthly",
            "service_rate": "consumption",
        }

        storage_allocation = create_allocation(self.project, self.user, form_data)

        new_rw_users: list = form_data["rw_users"].copy()
        new_rw_users.append("newuser")

        UpdateAllocationView.set_access_users("rw", new_rw_users, storage_allocation)

        access_allocation = AclAllocations.get_access_allocation(
            storage_allocation, "rw"
        )

        self.assertTrue(mock_async_task.called)
        args, kwargs = mock_async_task.call_args
        self.assertEqual(args[0], addMembersToADGroup)
        self.assertIn("newuser", args[1])
        self.assertEqual(args[2], access_allocation)

    def test_attribute_change_request_creation(
        self,
        mock_ActiveDirectoryAPI: MagicMock,
        mock_async_task: MagicMock,
        mock_file_system_service: MagicMock,
    ):
        # allocation and allocation attributes already created

        form = UpdateAllocationForm(data=self.form_data, user_id=self.user.id)
        form.cleaned_data = self.form_data
        form.clean()
        # No changes in the form data, so no AllocationAttributeChangeRequest should be created
        view = UpdateAllocationView(form=form, user_id=self.user.id)
        view.kwargs = {"allocation_id": self.storage_allocation.id}
        view._updated_fields_handler(
            form=form, parent_allocation=self.storage_allocation
        )
        self.assertEqual(len(AllocationAttributeChangeRequest.objects.all()), 0)

        # attributes change, so AllocationAttributeChangeRequest should be created
        updated_form_data = {
            "storage_filesystem_path": "foo",
            "storage_export_path": "bar",
            "storage_ticket": "ITSD-54321",
            "storage_name": "baz",
            "storage_quota": 17,
            "protocols": ["nfs"],
            "rw_users": ["test"],
            "ro_users": [],
            "cost_center": "Uncle Pennybags MUTATE",
            "billing_exempt": "No",
            "department_number": "Time Travel Services MUTATE",
            "billing_cycle": "monthly",
            "service_rate": "consumption",
            "technical_contact": "it.guru MUTATE",
            "billing_contact": "finance.guru MUTATE",
        }

        form = UpdateAllocationForm(data=updated_form_data, user_id=self.user.id)
        form.cleaned_data = updated_form_data
        form.clean()
        view = UpdateAllocationView(form=form, user_id=self.user.id)
        view.kwargs = {"allocation_id": self.storage_allocation.id}
        view._updated_fields_handler(
            form=form, parent_allocation=self.storage_allocation
        )
        self.assertEqual(len(AllocationAttributeChangeRequest.objects.all()), 5)
        value_changes = list(
            AllocationAttributeChangeRequest.objects.all().values_list(
                "new_value", flat=True
            )
        )
        self.assertEqual(
            value_changes,
            [
                "Uncle Pennybags MUTATE",
                "Time Travel Services MUTATE",
                "it.guru MUTATE",
                "finance.guru MUTATE",
                "17",
            ],
        )

    def test_attribute_change_request_creation_with_optional_attributes(
        self,
        mock_ActiveDirectoryAPI: MagicMock,
        mock_async_task: MagicMock,
        mock_file_system_service: MagicMock,
    ):
        form_data_missing_contacts = {
            "storage_filesystem_path": "foo_missing",
            "storage_export_path": "bar_missing",
            "storage_ticket": "ITSD-54321",
            "storage_name": "baz",
            "storage_quota": 7,
            "protocols": ["smb"],
            "rw_users": ["test"],
            "ro_users": [],
            "cost_center": "Internation Monetary Fund",
            "billing_exempt": "No",
            "department_number": "Time Travel Services",
            "billing_cycle": "monthly",
            "service_rate": "consumption",
        }

        storage_allocation_missing_contacts = create_allocation(
            self.project, self.user, form_data_missing_contacts
        )

        form = UpdateAllocationForm(
            data=form_data_missing_contacts, user_id=self.user.id
        )
        form_data_missing_contacts["billing_contact"] = "new_billing_contact"
        form_data_missing_contacts["technical_contact"] = "new_tech_contact"
        form.cleaned_data = form_data_missing_contacts
        form.clean()
        view = UpdateAllocationView(form=form, user_id=self.user.id)
        view.kwargs = {"allocation_id": storage_allocation_missing_contacts.id}
        view._updated_fields_handler(
            form=form, parent_allocation=storage_allocation_missing_contacts
        )
        self.assertEqual(len(AllocationAttributeChangeRequest.objects.all()), 2)
        value_changes = list(
            AllocationAttributeChangeRequest.objects.all().values_list(
                "new_value", flat=True
            )
        )
        self.assertEqual(
            value_changes,
            [
                "new_tech_contact",
                "new_billing_contact",
            ],
        )

        request = RequestFactory().post("/irrelevant")
        form = UpdateAllocationForm(
            data=form_data_missing_contacts, user_id=self.user.id
        )
        form_data_missing_contacts["billing_contact"] = "new_billing_contact"
        form_data_missing_contacts["technical_contact"] = "new_tech_contact"
        form.cleaned_data = form_data_missing_contacts
        form.clean()
        view = UpdateAllocationView(form=form, user_id=self.user.id)
        view.setup(request, allocation_id=storage_allocation_missing_contacts.id)
        view.success_id = 1

        view.form_valid(form)

        self.assertTrue(view.form_valid(form))

    def test_update_allocation_form_and_view_valid(
        self,
        mock_ActiveDirectoryAPI: MagicMock,
        mock_async_task: MagicMock,
        mock_file_system_service: MagicMock,
    ):
        response = UpdateAllocationView.as_view()(self.request, allocation_id=1)
        self.assertEqual(response.status_code, 200)

    def test_context_data_no_linkage(
        self,
        mock_ActiveDirectoryAPI: MagicMock,
        mock_async_task: MagicMock,
        mock_file_system_service: MagicMock,
    ):
        view = UpdateAllocationView(
            form=UpdateAllocationForm(data=self.form_data, user_id=self.user.id)
        )
        view.setup(self.request, allocation_id=1)
        self.assertFalse(
            dict(view.get_context_data()).get("allocation_has_children", True)
        )

    def test_context_data_with_linked_sub(
        self,
        mock_ActiveDirectoryAPI: MagicMock,
        mock_async_task: MagicMock,
        mock_file_system_service: MagicMock,
    ):
        sub_form_data = {
            "storage_filesystem_path": "foo",
            "storage_export_path": "bar",
            "storage_ticket": "ITSD-54321",
            "storage_name": "baz",
            "storage_quota": 7,
            "protocols": ["nfs"],
            "rw_users": ["test"],
            "ro_users": [],
            "cost_center": "Uncle Pennybags",
            "billing_exempt": "No",
            "department_number": "Time Travel Services",
            "billing_cycle": "monthly",
            "service_rate": "consumption",
            "technical_contact": "it.guru",
            "billing_contact": "finance.guru",
        }
        sub_allocation = create_allocation(
            self.project, self.user, sub_form_data, self.storage_allocation
        )
        view = UpdateAllocationView(
            form=UpdateAllocationForm(data=self.form_data, user_id=self.user.id)
        )
        view.setup(self.request, allocation_id=1)
        self.assertTrue(
            dict(view.get_context_data()).get("allocation_has_children", True)
        )

    def test_valid_form_with_reset_acls_calls_reset_acls(
        self,
        mock_ActiveDirectoryAPI: MagicMock,
        mock_async_task: MagicMock,
        mock_file_system_service: MagicMock,
    ):
        request = RequestFactory().post("/irrelevant", {"reset_acls": "set"})
        request.user = self.user
        form = UpdateAllocationForm(data=self.form_data, user_id=self.user.id)
        form.cleaned_data = {
            "protocols": ["smb"],
            "storage_export_path": "bar",
            "storage_ticket": "ITSD-12345",
            "storage_filesystem_path": "/storage2-dev/fs1/allocationName",
        }
        form.clean()
        view = UpdateAllocationView(form=form, user_id=self.user.id)
        view.setup(request, allocation_id=1)
        view.success_id = 1
        view._reset_acls = MagicMock()
        view._updated_fields_handler = MagicMock()
        self.assertTrue(view.form_valid(form))
        view._reset_acls.assert_called_once()
        view._updated_fields_handler.assert_not_called()

    def test_reset_acls_runs_task_with_valid_args(
        self,
        mock_ActiveDirectoryAPI: MagicMock,
        mock_async_task: MagicMock,
        mock_file_system_service: MagicMock,
    ):
        for onOff, trueFalse in {"on": True, "off": False}.items():
            messages.add_message = MagicMock()
            request = RequestFactory().post(
                "/irrelevant",
                {"reset_acls": "set", "reset_sub_acls": "on" if onOff == "on" else ""},
            )
            request.user = self.user
            form = UpdateAllocationForm(data=self.form_data, user_id=self.user.id)
            form.cleaned_data = {
                "project_pk": self.project.id,
                "protocols": ["smb"],
                "rw_users": ["test"],
                "ro_users": ["test2"],
                "storage_export_path": "bar",
                "storage_filesystem_path": "updatedFormPath",
                "storage_name": "foo",
                "storage_ticket": "ITSD-12345",
            }
            form.clean()
            view = UpdateAllocationView(form=form, user_id=self.user.id)
            view.setup(request, allocation_id=1)
            view.success_id = 1

            self.assertTrue(view.form_valid(form))
            mock_async_task.assert_called_with(
                reset_allocation_acls,
                self.user.email,
                self.storage_allocation,
                trueFalse,
                hook=acl_reset_complete_hook,
                q_options={"retry": 90000, "timeout": 86400},
            )

    def test_identify_new_form_values(
        self,
        mock_ActiveDirectoryAPI: MagicMock,
        mock_async_task: MagicMock,
        mock_file_system_service: MagicMock,
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
            "cost_center": "Caroline Cost Center",
            "billing_exempt": "No",
            "department_number": "Time Travel Services",
            "billing_cycle": "monthly",
            "service_rate": "consumption",
            "technical_contact": "it.guru",
            "billing_contact": "finance.guru",
        }

        alloc = self.storage_allocation

        attributes_to_check = [
            "cost_center",
            "billing_exempt",
            "department_number",
            "billing_cycle",
            "technical_contact",
            "billing_contact",
            "service_rate",
            "storage_ticket",
            "storage_quota",
        ]

        form_values = [form_data.get(field_name) for field_name in attributes_to_check]

        attributes_to_check.append("storage_protocols")
        form_values.append(json.dumps(form_data.get("protocols")))

        attribute_changes = list(zip(attributes_to_check, form_values))

        try:
            new_values = UpdateAllocationView._identify_new_form_values(
                alloc, attributes_to_check, attribute_changes
            )
        except:
            print("Unable to compare values")
