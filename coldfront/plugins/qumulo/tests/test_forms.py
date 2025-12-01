import json
import os
import json

from django.test import TestCase
from unittest.mock import patch

from django.contrib.auth.models import Permission

from coldfront.core.allocation.models import AllocationStatusChoice
from coldfront.core.project.models import Project, ProjectStatusChoice
from coldfront.core.resource.models import Resource
from coldfront.core.user.models import User
from coldfront.core.field_of_science.models import FieldOfScience

from coldfront.plugins.qumulo.forms.ProjectCreateForm import ProjectCreateForm
from coldfront.plugins.qumulo.forms.AllocationForm import AllocationForm
from coldfront.plugins.qumulo.forms.UpdateAllocationForm import UpdateAllocationForm
from coldfront.plugins.qumulo.tests.helper_classes.filesystem_path import (
    PathExistsMock,
    ValidFormPathMock,
)
from coldfront.plugins.qumulo.tests.utils.mock_data import (
    build_models,
    build_models_without_project,
    create_allocation,
    mock_qumulo_info,
)


@patch.dict(os.environ, {"QUMULO_INFO": json.dumps(mock_qumulo_info)})
class AllocationFormTests(TestCase):
    def setUp(self):
        build_data = build_models()
        self.qumulo_patcher = patch(
            "coldfront.plugins.qumulo.utils.storage_controller.StorageControllerFactory.create_connection"
        )
        self.mock_qumulo_api = self.qumulo_patcher.start()

        self.active_directory_patcher = patch(
            "coldfront.plugins.qumulo.validators.ActiveDirectoryAPI"
        )
        self.mock_active_directory_api = self.active_directory_patcher.start()
        self.mock_active_directory_api.return_value.get_members.return_value = [
            {"attributes": {"sAMAccountName": "test"}}
        ]

        self.qumulo_info = json.loads(os.environ.get("QUMULO_INFO"))
        self.old_storage2_path = self.qumulo_info["Storage2"]["path"]
        self.qumulo_info["Storage2"]["path"] = "/path/to"

        self.user = build_data["user"]
        self.project1 = build_data["project"]

        self.activeStatus = self.project1.status
        self.fieldOfScience = self.project1.field_of_science
        self._setupValidPathQumuloAPI()

    def tearDown(self):
        self.qumulo_patcher.stop()
        patch.stopall()

        self.qumulo_info["Storage2"]["path"] = self.old_storage2_path
        return super().tearDown()

    def _setupPathExistsMock(self):
        self.mock_qumulo_api.return_value.rc.fs.get_file_attr = PathExistsMock()

    def _setupValidPathQumuloAPI(self):
        self.mock_qumulo_api.return_value.rc.fs.get_file_attr = ValidFormPathMock()

    def test_clean_method_with_valid_data(self):
        data = {
            "project_pk": self.project1.id,
            "storage_type": "Storage2",
            "storage_name": "TestAllocation",
            "storage_quota": 1000,
            "protocols": ["nfs"],
            "storage_filesystem_path": "path_to_filesystem",
            "storage_ticket": "ITSD-98765",
            "storage_export_path": "/path/to/export",
            "rw_users": ["test"],
            "ro_users": ["test"],
            "cost_center": "Uncle Pennybags",
            "billing_exempt": "No",
            "department_number": "Time Travel Services",
            "billing_cycle": "monthly",
            "service_rate_category": "consumption",
        }
        form = AllocationForm(data=data, user_id=self.user.id)
        self.assertTrue(form.is_valid())

    def test_clean_method_with_invalid_data(self):
        data = {
            "project_pk": self.project1.id,
            "storage_type": "Storage2",
            "storage_name": "Test Allocation",
            "storage_quota": 1000,
            "protocols": ["nfs"],
            "storage_filesystem_path": "path_to_filesystem",
            "storage_ticket": "ITSD-98765",
            "storage_export_path": "",  # Missing export path for NFS
            "rw_users": ["test"],
            "ro_users": ["test"],
            "cost_center": "Uncle Pennybags",
            "billing_exempt": "No",
            "department_number": "Time Travel Services",
            "billing_cycle": "monthly",
            "service_rate_category": "consumption",
        }
        form = AllocationForm(data=data, user_id=self.user.id)
        self.assertFalse(form.is_valid())

    def test_duplicate_storage_name_for_storage_type(self):
        # First, create an allocation with a specific name
        existing_allocation_data = {
            "project_pk": self.project1.id,
            "storage_type": "Storage2",
            "storage_name": "duplicatename",
            "storage_quota": 1000,
            "protocols": ["nfs"],
            "storage_filesystem_path": "path_to_filesystem",
            "storage_ticket": "ITSD-12345",
            "storage_export_path": "/path/to/export",
            "rw_users": ["test"],
            "ro_users": ["test"],
            "cost_center": "Uncle Pennybags",
            "billing_exempt": "No",
            "department_number": "Time Travel Services",
            "billing_cycle": "monthly",
            "service_rate_category": "consumption",
        }
        create_allocation(self.project1, self.user, existing_allocation_data)

        # Now, attempt to create another allocation with the same name
        duplicate_name_data = {
            "project_pk": self.project1.id,
            "storage_type": "Storage2",
            "storage_name": "duplicatename",  # Same name as existing allocation
            "storage_quota": 2000,
            "protocols": ["nfs"],
            "storage_filesystem_path": "another_path_to_filesystem",
            "storage_ticket": "ITSD-67890",
            "storage_export_path": "/another/path/to/export",
            "rw_users": ["test"],
            "ro_users": ["test"],
            "cost_center": "Uncle Pennybags",
            "billing_exempt": "No",
            "department_number": "Time Travel Services",
            "billing_cycle": "monthly",
            "service_rate_category": "consumption",
        }
        form = AllocationForm(data=duplicate_name_data, user_id=self.user.id)
        self.assertFalse(form.is_valid())
        self.assertIn("storage_name", form.errors)

        # Now, attempt to create another allocation with the same name but different storage type
        duplicate_name_data_different_storage_type = {
            "project_pk": self.project1.id,
            "storage_type": "Storage3",
            "storage_name": "duplicatename",  # Same name as existing allocation
            "storage_quota": 2000,
            "protocols": ["nfs"],
            "storage_filesystem_path": "another_path_to_filesystem",
            "storage_ticket": "ITSD-67890",
            "storage_export_path": "/another/path/to/export",
            "rw_users": ["test"],
            "ro_users": ["test"],
            "cost_center": "Uncle Pennybags",
            "billing_exempt": "No",
            "department_number": "Time Travel Services",
            "billing_cycle": "monthly",
            "service_rate_category": "consumption",
        }
        form = AllocationForm(
            data=duplicate_name_data_different_storage_type, user_id=self.user.id
        )
        self.assertTrue(form.is_valid())
        self.assertNotIn("storage_name", form.errors)

        # Now, attempt to create another allocation with an allocation attribute other than storage_name having the same name
        duplicate_name_data_in_another_allocation_attribute = {
            "project_pk": self.project1.id,
            "storage_type": "Storage3",
            "storage_name": "just_a_name",  # Same name as existing allocation
            "storage_quota": 2000,
            "protocols": ["nfs"],
            "storage_filesystem_path": "another_path_to_filesystem",
            "storage_ticket": "ITSD-67890",
            "storage_export_path": "/another/path/to/export",
            "rw_users": ["test"],
            "ro_users": ["test"],
            "cost_center": "duplicatename",
            "billing_exempt": "No",
            "department_number": "Time Travel Services",
            "billing_cycle": "monthly",
            "service_rate_category": "consumption",
        }
        form = AllocationForm(
            data=duplicate_name_data_in_another_allocation_attribute,
            user_id=self.user.id,
        )
        self.assertTrue(form.is_valid())
        self.assertNotIn("storage_name", form.errors)
        self.assertNotIn("cost_center", form.errors)


    def test_empty_ro_users_form_valid(self):
        data = {
            "project_pk": self.project1.id,
            "storage_type": "Storage2",
            "storage_name": "valid-smb-allocation-name",
            "storage_quota": 1000,
            "protocols": ["smb"],
            "ro_users": ["test"],
            "rw_users": ["test"],
            "storage_filesystem_path": "path_to_filesystem",
            "storage_ticket": "ITSD-98765",
            "storage_export_path": "",
            "cost_center": "Uncle Pennybags",
            "billing_exempt": "No",
            "department_number": "Time Travel Services",
            "billing_cycle": "monthly",
            "service_rate_category": "consumption",
        }
        form = AllocationForm(data=data, user_id=self.user.id)
        self.assertFalse(form.fields["ro_users"].required)
        self.assertTrue(form.is_valid())

    def test_storage_ticket_required(self):
        data = {
            "project_pk": self.project1.id,
            "storage_type": "Storage2",
            "storage_name": "valid-smb-allocation-name",
            "storage_quota": 1000,
            "protocols": ["smb"],
            "ro_users": [],
            "rw_users": ["test"],
            "storage_filesystem_path": "path_to_filesystem",
            # "storage_ticket": "ITSD-98765",
            "storage_export_path": "",
            "cost_center": "Uncle Pennybags",
            "billing_exempt": "No",
            "department_number": "Time Travel Services",
            "billing_cycle": "monthly",
            "service_rate_category": "consumption",
        }
        form = AllocationForm(data=data, user_id=self.user.id)
        self.assertTrue(form.fields["storage_ticket"].required)
        self.assertFalse(form.is_valid())

    def test_billing_exempt_required(self):
        invalid_data = {
            "project_pk": self.project1.id,
            "storage_type": "Storage2",
            "storage_name": "valid-smb-allocation-name",
            "storage_quota": 1000,
            "protocols": ["smb"],
            "ro_users": [],
            "rw_users": ["test"],
            "storage_filesystem_path": "path_to_filesystem",
            "storage_ticket": "ITSD-98765",
            "storage_export_path": "",
            "cost_center": "Uncle Pennybags",
            # "billing_exempt": "No",
            "department_number": "Time Travel Services",
            "billing_cycle": "monthly",
            "service_rate_category": "consumption",
        }
        invalid_form = AllocationForm(data=invalid_data, user_id=self.user.id)
        self.assertTrue(invalid_form.fields["billing_exempt"].required)
        self.assertFalse(invalid_form.is_valid())

    # The value of billing_exempt is casesensitive, which will only take "Yes" or "No".
    def test_billing_exempt_invalid_values(self):
        invalid_values = {True, False, "yes", "no", "YES", "NO", "Yes/No", "abc", ""}
        for invalid_value in invalid_values:
            invalid_data = {
                "project_pk": self.project1.id,
                "storage_type": "Storage2",
                "storage_name": "valid-smb-allocation-name",
                "storage_quota": 1000,
                "protocols": ["smb"],
                "ro_users": [],
                "rw_users": ["test"],
                "storage_filesystem_path": "path_to_filesystem",
                "storage_ticket": "ITSD-98765",
                "storage_export_path": "",
                "cost_center": "Uncle Pennybags",
                "billing_exempt": invalid_value,
                "department_number": "Time Travel Services",
                "billing_cycle": "monthly",
                "service_rate_category": "consumption",
            }
            invalid_form = AllocationForm(data=invalid_data, user_id=self.user.id)
            self.assertFalse(invalid_form.is_valid())

    def test_billing_exempt_is_Yes(self):
        data = {
            "project_pk": self.project1.id,
            "storage_type": "Storage2",
            "storage_name": "valid-smb-allocation-name",
            "storage_quota": 1000,
            "protocols": ["smb"],
            "ro_users": [],
            "rw_users": ["test"],
            "storage_filesystem_path": "path_to_filesystem",
            "storage_ticket": "ITSD-98765",
            "storage_export_path": "",
            "cost_center": "Uncle Pennybags",
            "billing_exempt": "Yes",
            "department_number": "Time Travel Services",
            "billing_cycle": "monthly",
            "service_rate_category": "consumption",
        }
        form = AllocationForm(data=data, user_id=self.user.id)
        self.assertTrue(form.is_valid())

    def test_billing_exempt_is_No(self):
        data = {
            "project_pk": self.project1.id,
            "storage_type": "Storage2",
            "storage_name": "valid-smb-allocation-name",
            "storage_quota": 1000,
            "protocols": ["smb"],
            "ro_users": [],
            "rw_users": ["test"],
            "storage_filesystem_path": "path_to_filesystem",
            "storage_ticket": "ITSD-98765",
            "storage_export_path": "",
            "cost_center": "Uncle Pennybags",
            "billing_exempt": "No",
            "department_number": "Time Travel Services",
            "billing_cycle": "monthly",
            "service_rate_category": "consumption",
        }
        form = AllocationForm(data=data, user_id=self.user.id)
        form.is_valid()
        self.assertTrue(form.is_valid())

    def test_billing_cycle_required(self):
        invalid_data = {
            "project_pk": self.project1.id,
            "storage_type": "Storage2",
            "storage_name": "valid-smb-allocation-name",
            "storage_quota": 1000,
            "protocols": ["smb"],
            "ro_users": [],
            "rw_users": ["test"],
            "storage_filesystem_path": "path_to_filesystem",
            "storage_ticket": "ITSD-98765",
            "storage_export_path": "",
            "cost_center": "Uncle Pennybags",
            "billing_exempt": "No",
            "department_number": "Time Travel Services",
            # "billing_cycle": "monthly",
            "service_rate_category": "not_a_rate",
        }
        invalid_form = AllocationForm(data=invalid_data, user_id=self.user.id)
        self.assertTrue(invalid_form.fields["billing_cycle"].required)
        self.assertFalse(invalid_form.is_valid())

    def test_service_rate_valid_options(self):
        invalid_data = {
            "project_pk": self.project1.id,
            "storage_type": "Storage2",
            "storage_name": "valid-smb-allocation-name",
            "storage_quota": 1000,
            "protocols": ["smb"],
            "ro_users": [],
            "rw_users": ["test"],
            "storage_filesystem_path": "path_to_filesystem",
            "storage_ticket": "ITSD-98765",
            "storage_export_path": "",
            "cost_center": "Uncle Pennybags",
            "billing_exempt": "No",
            "department_number": "Time Travel Services",
            "billing_cycle": "monthly",
            "service_rate_category": "not_a_rate",
        }
        invalid_form = AllocationForm(data=invalid_data, user_id=self.user.id)
        self.assertTrue(invalid_form.fields["service_rate_category"].required)
        self.assertFalse(invalid_form.is_valid())

        valid_data = {
            "project_pk": self.project1.id,
            "storage_type": "Storage2",
            "storage_name": "valid-smb-allocation-name",
            "storage_quota": 1000,
            "protocols": ["smb"],
            "ro_users": [],
            "rw_users": ["test"],
            "storage_filesystem_path": "path_to_filesystem",
            "storage_ticket": "ITSD-98765",
            "storage_export_path": "",
            "cost_center": "Uncle Pennybags",
            "billing_exempt": "No",
            "department_number": "Time Travel Services",
            "billing_cycle": "monthly",
            "service_rate_category": "consumption",
        }
        valid_form = AllocationForm(data=valid_data, user_id=self.user.id)
        self.assertTrue(valid_form.fields["service_rate_category"].required)
        self.assertTrue(valid_form.is_valid())

    def test_empty_technical_contact(self):
        data = {
            "project_pk": self.project1.id,
            "storage_type": "Storage2",
            "storage_name": "valid-smb-allocation-name",
            "storage_quota": 1000,
            "protocols": ["smb"],
            "ro_users": [],
            "rw_users": ["test"],
            "storage_filesystem_path": "path_to_filesystem",
            "storage_ticket": "ITSD-98765",
            "storage_export_path": "",
            "cost_center": "Uncle Pennybags",
            "billing_exempt": "No",
            "department_number": "Time Travel Services",
            "billing_cycle": "monthly",
            "service_rate_category": "consumption",
        }
        form = AllocationForm(data=data, user_id=self.user.id)
        self.assertFalse(form.fields["technical_contact"].required)
        self.assertTrue(form.is_valid())

    def test_provided_technical_contact(self):
        data = {
            "project_pk": self.project1.id,
            "storage_type": "Storage2",
            "storage_name": "valid-smb-allocation-name",
            "storage_quota": 1000,
            "protocols": ["smb"],
            "ro_users": [],
            "rw_users": ["test"],
            "storage_filesystem_path": "path_to_filesystem",
            "storage_ticket": "ITSD-98765",
            "storage_export_path": "",
            "cost_center": "Uncle Pennybags",
            "billing_exempt": "No",
            "department_number": "Time Travel Services",
            "billing_cycle": "monthly",
            "service_rate_category": "consumption",
            "technical_contact": "captain.crunch",
        }
        form = AllocationForm(data=data, user_id=self.user.id)
        self.assertFalse(form.fields["technical_contact"].required)
        self.assertTrue(form.is_valid())

    def test_empty_billing_contact(self):
        data = {
            "project_pk": self.project1.id,
            "storage_type": "Storage2",
            "storage_name": "valid-smb-allocation-name",
            "storage_quota": 1000,
            "protocols": ["smb"],
            "ro_users": [],
            "rw_users": ["test"],
            "storage_filesystem_path": "path_to_filesystem",
            "storage_ticket": "ITSD-98765",
            "storage_export_path": "",
            "cost_center": "Uncle Pennybags",
            "billing_exempt": "No",
            "department_number": "Time Travel Services",
            "billing_cycle": "monthly",
            "service_rate_category": "consumption",
        }
        form = AllocationForm(data=data, user_id=self.user.id)
        self.assertFalse(form.fields["billing_contact"].required)
        self.assertTrue(form.is_valid())

    def test_provided_billing_contact(self):
        data = {
            "project_pk": self.project1.id,
            "storage_type": "Storage2",
            "storage_name": "valid-smb-allocation-name",
            "storage_quota": 1000,
            "protocols": ["smb"],
            "ro_users": [],
            "rw_users": ["test"],
            "storage_filesystem_path": "path_to_filesystem",
            "storage_ticket": "ITSD-98765",
            "storage_export_path": "",
            "cost_center": "Uncle Pennybags",
            "billing_exempt": "No",
            "department_number": "Time Travel Services",
            "service_rate_category": "consumption",
            "billing_contact": "captain.crunch",
            "billing_cycle": "monthly",
        }
        form = AllocationForm(data=data, user_id=self.user.id)
        self.assertFalse(form.fields["billing_contact"].required)
        self.assertTrue(form.is_valid())

    def test_default_rw_user_required(self):
        valid_data = {
            "project_pk": self.project1.id,
            "storage_name": "valid-smb-allocation-name",
            "storage_quota": 1000,
            "protocols": ["smb"],
            "ro_users": [],
            "rw_users": ["test"],
            "storage_filesystem_path": "path_to_filesystem",
            "storage_ticket": "ITSD-98765",
            "storage_export_path": "",
            "cost_center": "Uncle Pennybags",
            "billing_exempt": "No",
            "department_number": "Time Travel Services",
            "billing_cycle": "monthly",
            "service_rate_category": "consumption",
        }
        form = AllocationForm(data=valid_data, user_id=self.user.id)
        self.assertTrue(form.fields["rw_users"].required)


class AllocationFormProjectChoiceTests(TestCase):
    def setUp(self):
        build_models_without_project()
        self.patcher = patch("coldfront.plugins.qumulo.validators.QumuloAPI")
        self.mock_qumulo_api = self.patcher.start()

        self.activeStatus = ProjectStatusChoice.objects.get(name="Active")
        self.fieldOfScience = FieldOfScience.objects.create(description="test")

        self.user_a = User.objects.create(username="test_a", password="test_a")
        # user_b is a superuser and should be able to see both projects
        self.user_b = User.objects.create(
            username="test_b", password="test_b", is_superuser=True
        )

        self.project_a = Project.objects.create(
            title="Project A",
            pi=self.user_a,
            status=self.activeStatus,
            field_of_science=self.fieldOfScience,
        )

        self.project_b = Project.objects.create(
            title="Project B",
            pi=self.user_b,
            status=self.activeStatus,
            field_of_science=self.fieldOfScience,
        )

        self.data_a = {
            "project_pk": self.project_a.id,
            "storage_name": "Test Allocation",
            "storage_quota": 1000,
            "protocols": ["nfs"],
            "storage_filesystem_path": "path_to_filesystem",
            "storage_ticket": "ITSD-98765",
            "storage_export_path": "/path/to/export",
            "rw_users": ["test"],
            "ro_users": ["test"],
            "cost_center": "Uncle Pennybags",
            "billing_exempt": "No",
            "department_number": "Time Travel Services",
            "billing_cycle": "monthly",
            "service_rate_category": "consumption",
        }
        self.form_a = AllocationForm(data=self.data_a, user_id=self.user_a.id)

        self.data_b = {
            "project_pk": self.project_b.id,
            "storage_name": "Test Allocation",
            "storage_quota": 1000,
            "protocols": ["nfs"],
            "storage_filesystem_path": "path_to_filesystem",
            "storage_ticket": "ITSD-98765",
            "storage_export_path": "/path/to/export",
            "rw_users": ["test"],
            "ro_users": ["test"],
            "cost_center": "Uncle Pennybags",
            "billing_exempt": "No",
            "department_number": "Time Travel Services",
            "billing_cycle": "monthly",
            "service_rate_category": "consumption",
        }
        self.form_b = AllocationForm(data=self.data_b, user_id=self.user_b.id)

    def tearDown(self):
        self.patcher.stop()
        return super().tearDown()

    def test_project_visibility(self):

        projects_for_a = [entry for entry in self.form_a.get_project_choices()]
        projects_for_b = [entry for entry in self.form_b.get_project_choices()]

        self.assertEqual(projects_for_a, [(self.project_a.id, self.project_a.title)])

        self.assertEqual(
            projects_for_b,
            [
                (self.project_a.id, self.project_a.title),
                (self.project_b.id, self.project_b.title),
            ],
        )

    def test_project_visibility_perm_check(self):

        perm = Permission.objects.get(codename="can_view_all_projects")

        self.user_a.user_permissions.add(perm)

        projects_for_a = [entry for entry in self.form_a.get_project_choices()]

        self.assertEqual(
            projects_for_a,
            [
                (self.project_a.id, self.project_a.title),
                (self.project_b.id, self.project_b.title),
            ],
        )


@patch("coldfront.plugins.qumulo.validators.ActiveDirectoryAPI")
class ProjectFormTests(TestCase):
    def setUp(self):
        self.fieldOfScience = FieldOfScience.objects.create(description="Bummerology")

    def test_form_with_valid_data(self, mock_active_directory_api):
        valid_data = {
            "title": "project-sleong",
            "pi": "sleong",
            "description": "This is the description for the project",
            "field_of_science": self.fieldOfScience.id,
        }
        form = ProjectCreateForm(data=valid_data, user_id="admin")
        self.assertTrue(form.is_valid())


class UpdateAllocationFormTests(TestCase):
    def setUp(self):
        build_data = build_models()
        self.user = build_data["user"]
        self.project1 = build_data["project"]
        storage2 = Resource.objects.get(name="Storage2")
        self.initial = {
            "storage_name": "TestAllocation",
            "storage_filesystem_path": "path_to_filesystem",
            "storage_type": storage2.name,
        }
        self.data = {
            "project_pk": self.project1.id,
            "storage_quota": 1000,
            "protocols": ["nfs"],
            "storage_ticket": "ITSD-98765",
            "storage_export_path": "/path/to/export",
            "rw_users": ["test"],
            "ro_users": ["test"],
            "cost_center": "Uncle Pennybags",
            "billing_exempt": "No",
            "department_number": "Time Travel Services",
            "billing_cycle": "monthly",
            "service_rate_category": "consumption",
        }
        self.data_for_creation = {**self.data, **self.initial}
        self.allocation = create_allocation(self.project1, self.user, self.data_for_creation)

    def tearDown(self):
        return super().tearDown()

    def test_default_rw_users_required(self):
        form = UpdateAllocationForm(
            initial=self.initial,
            allocation_status_name=self.allocation.status.name,
            data=self.data,
            user_id=self.user.id,
        )
        self.assertTrue(form.fields["rw_users"].required)

    def test_ready_for_deletion_rw_users_not_required(self):
        rfd_status = AllocationStatusChoice.objects.filter(
            name="Ready for deletion"
        ).first()
        self.allocation.status = rfd_status
        self.allocation.save()
        form = UpdateAllocationForm(
            initial=self.initial,
            allocation_status_name=self.allocation.status.name,
            data=self.data,
            user_id=self.user.id,
        )
        self.assertTrue(form.is_valid())
        self.assertFalse(form.fields["rw_users"].required)

    def test_validations_on_changed_values(self):
        update_form = UpdateAllocationForm(
            initial=self.initial, data=self.data, user_id=self.user.id
        )
        self.assertTrue(update_form.is_bound)
        self.assertTrue(update_form.is_valid())
        update_form.clean()
        self.assertNotIn("storage_name", update_form.errors)
        self.assertNotIn("storage_type", update_form.errors)
        self.assertEqual(len(update_form.errors), 0)
