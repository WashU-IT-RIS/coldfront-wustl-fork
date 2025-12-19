from django.test import TestCase
from unittest.mock import patch, MagicMock

from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttributeType,
    AllocationAttribute,
)

from coldfront.plugins.qumulo.tests.utils.mock_data import build_models
from coldfront.plugins.qumulo.services.allocation_service import AllocationService
from coldfront.plugins.qumulo.views.allocation_view import AllocationView
from coldfront.plugins.qumulo.validators import existing_project_quota, update_calculate_total_project_quotas, create_calculate_total_project_quotas

@patch("coldfront.plugins.qumulo.services.allocation_service.ActiveDirectoryAPI")
@patch("coldfront.plugins.qumulo.services.allocation_service.async_task")
@patch("coldfront.plugins.qumulo.validators.ActiveDirectoryAPI")
class CondoQuotaValidationTest(TestCase):
    def setUp(self):
        build_data = build_models()

        self.project = build_data["project"]
        self.user = build_data["user"]

        self.client.force_login(self.user)

        self.form_data = {
            "project_pk": self.project.id,
            "storage_type": "Storage2",
            "storage_filesystem_path": "foo",
            "storage_export_path": "bar",
            "storage_ticket": "ITSD-54321",
            "storage_name": "baz",
            "storage_quota": 7,
            "protocols": ["nfs"],
            "rw_users": ["test"],
            "ro_users": ["test1"],
            "cost_center": "Uncle Pennybags",
            "billing_exempt": "No",
            "department_number": "Time Travel Services",
            "billing_cycle": "monthly",
            "service_rate_category": "consumption",
        }

    def test_existing_condo_quota_no_allocs(self, mock_ActiveDirectoryValidator: MagicMock,mock_async_task: MagicMock,mock_ActiveDirectoryAPI: MagicMock,):
        breakpoint()
        total_quota = existing_project_quota(self.form_data["project_pk"])
        self.assertEqual(total_quota, 0)
    
    def test_sum_project_quotas(self, mock_ActiveDirectoryValidator: MagicMock,mock_async_task: MagicMock,mock_ActiveDirectoryAPI: MagicMock,):
        AllocationService.create_new_allocation(self.form_data, self.user)
        AllocationService.create_new_allocation(self.form_data, self.user)
        AllocationService.create_new_allocation(self.form_data, self.user)

        total_quotas = create_calculate_total_project_quotas(
            self.form_data["project_pk"], self.form_data["storage_quota"]
        )

        self.assertEqual(total_quotas, 28)
    
    def test_update_calculate_total_project_quotas_larger(self, mock_ActiveDirectoryValidator: MagicMock,mock_async_task: MagicMock,mock_ActiveDirectoryAPI: MagicMock,):
        AllocationService.create_new_allocation(self.form_data, self.user)
        AllocationService.create_new_allocation(self.form_data, self.user)
        AllocationService.create_new_allocation(self.form_data, self.user)
        AllocationService.create_new_allocation(self.form_data, self.user)

        current_quota = self.form_data["storage_quota"]
        project_pk = self.form_data["project_pk"]
        storage_quota = 25

        updated_total_quotas = update_calculate_total_project_quotas(project_pk, storage_quota, current_quota)

        self.assertEqual(updated_total_quotas, 46)

    def test_update_calculate_total_project_quotas_smaller(self, mock_ActiveDirectoryValidator: MagicMock,mock_async_task: MagicMock,mock_ActiveDirectoryAPI: MagicMock,):
        AllocationService.create_new_allocation(self.form_data, self.user)
        AllocationService.create_new_allocation(self.form_data, self.user)
        AllocationService.create_new_allocation(self.form_data, self.user)
        AllocationService.create_new_allocation(self.form_data, self.user)

        current_quota = self.form_data["storage_quota"]
        project_pk = self.form_data["project_pk"]
        storage_quota = 5

        updated_total_quotas = update_calculate_total_project_quotas(project_pk, storage_quota, current_quota)

        self.assertEqual(updated_total_quotas, 26)
