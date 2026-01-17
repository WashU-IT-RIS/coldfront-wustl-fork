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
from coldfront.plugins.qumulo.validators import validate_storage2_quota_increase

@patch("coldfront.plugins.qumulo.services.allocation_service.ActiveDirectoryAPI")
@patch("coldfront.plugins.qumulo.services.allocation_service.async_task")
@patch("coldfront.plugins.qumulo.validators.ActiveDirectoryAPI")
class Storage2QuotaValidationTest(TestCase):
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
    
    def test_storage2_quota_increase_below_threshold(self, mock_ActiveDirectoryValidator: MagicMock,mock_async_task: MagicMock,mock_ActiveDirectoryAPI: MagicMock,):
        allocation = AllocationService.create_new_allocation(self.form_data, self.user)

        current_quota = self.form_data["storage_quota"]
        new_storage_quota = 15

        try:
            validate_storage2_quota_increase(new_storage_quota, current_quota)
        except Exception as e:
            self.fail(f"Quota increase below threshold raised an exception: {e}")
    
    def test_storage2_quota_increase_above_threshold(self, mock_ActiveDirectoryValidator: MagicMock,mock_async_task: MagicMock,mock_ActiveDirectoryAPI: MagicMock,):
        allocation = AllocationService.create_new_allocation(self.form_data, self.user)

        current_quota = self.form_data["storage_quota"]
        new_storage_quota = 25

        with self.assertRaisesMessage(
            Exception,
            "Increases of 10TB or more for Storage2 allocations require approval. Please contact support.",
        ):
            validate_storage2_quota_increase(new_storage_quota, current_quota)