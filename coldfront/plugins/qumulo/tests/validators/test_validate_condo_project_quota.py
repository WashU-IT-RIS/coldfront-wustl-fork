from django.test import TestCase
from unittest.mock import patch, MagicMock

from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttributeType,
    AllocationAttribute,
)

from coldfront.plugins.qumulo.tests.utils.mock_data import build_models, default_form_data
from coldfront.plugins.qumulo.services.allocation_service import AllocationService
from coldfront.plugins.qumulo.views.allocation_view import AllocationView
from coldfront.plugins.qumulo.validators import existing_project_quota, update_calculate_total_project_quotas, create_calculate_total_project_quotas, calculate_remaining_condo_quota

@patch("coldfront.plugins.qumulo.services.allocation_service.ActiveDirectoryAPI")
@patch("coldfront.plugins.qumulo.services.allocation_service.async_task")
@patch("coldfront.plugins.qumulo.validators.ActiveDirectoryAPI")
class CondoQuotaValidationTest(TestCase):
    def setUp(self):
        build_data = build_models()

        self.project = build_data["project"]
        self.user = build_data["user"]

        self.client.force_login(self.user)
    
    def test_calculate_remaining_condo_quota(self, mock_ActiveDirectoryValidator: MagicMock,mock_async_task: MagicMock,mock_ActiveDirectoryAPI: MagicMock,):
        num_allocations = 2
        for i in range(num_allocations):
            form_data = default_form_data.copy()
            form_data["project_pk"] = self.project.pk
            form_data["storage_filesystem_path"] = f"test_path_{i}"
            AllocationService.create_new_allocation(form_data, self.user)

        remaining_quota = calculate_remaining_condo_quota(self.project.pk)
        self.assertEqual(remaining_quota, 986)
    
    def test_existing_condo_quota_with_allocs(self, mock_ActiveDirectoryValidator: MagicMock,mock_async_task: MagicMock,mock_ActiveDirectoryAPI: MagicMock,):
        num_allocations = 2
        for i in range(num_allocations):
            form_data = default_form_data.copy()
            form_data["project_pk"] = self.project.pk
            form_data["storage_filesystem_path"] = f"test_path_{i}"
            AllocationService.create_new_allocation(form_data, self.user)

        total_quota = existing_project_quota(self.project.pk)
        self.assertEqual(total_quota, 14)

    def test_existing_condo_quota_no_allocs(self, mock_ActiveDirectoryValidator: MagicMock,mock_async_task: MagicMock,mock_ActiveDirectoryAPI: MagicMock,):
        total_quota = existing_project_quota(self.project.pk)
        self.assertEqual(total_quota, 0)
    
    def test_sum_project_quotas(self, mock_ActiveDirectoryValidator: MagicMock,mock_async_task: MagicMock,mock_ActiveDirectoryAPI: MagicMock,):
        num_allocations = 3
        for i in range(num_allocations):
            form_data = default_form_data.copy()
            form_data["project_pk"] = self.project.pk
            form_data["storage_filesystem_path"] = f"test_path_{i}"
            AllocationService.create_new_allocation(form_data, self.user)

        total_quotas = create_calculate_total_project_quotas(
            self.project.pk, form_data["storage_quota"]
        )

        self.assertEqual(total_quotas, 28)
    
    def test_update_calculate_total_project_quotas_larger(self, mock_ActiveDirectoryValidator: MagicMock,mock_async_task: MagicMock,mock_ActiveDirectoryAPI: MagicMock,):
        num_allocations = 4
        for i in range(num_allocations):
            form_data = default_form_data.copy()
            form_data["project_pk"] = self.project.pk
            form_data["storage_filesystem_path"] = f"test_path_{i}"
            AllocationService.create_new_allocation(form_data, self.user)

        current_quota = form_data["storage_quota"]
        project_pk = self.project.pk
        storage_quota = 25

        updated_total_quotas = update_calculate_total_project_quotas(project_pk, storage_quota, current_quota)

        self.assertEqual(updated_total_quotas, 46)

    def test_update_calculate_total_project_quotas_smaller(self, mock_ActiveDirectoryValidator: MagicMock,mock_async_task: MagicMock,mock_ActiveDirectoryAPI: MagicMock,):
        num_allocations = 4
        for i in range(num_allocations):
            form_data = default_form_data.copy()
            form_data["project_pk"] = self.project.pk
            form_data["storage_filesystem_path"] = f"test_path_{i}"
            AllocationService.create_new_allocation(form_data, self.user)

        current_quota = form_data["storage_quota"]
        project_pk = self.project.pk
        storage_quota = 5

        updated_total_quotas = update_calculate_total_project_quotas(project_pk, storage_quota, current_quota)

        self.assertEqual(updated_total_quotas, 26)
