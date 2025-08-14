from django.test import Client, TestCase, RequestFactory
from django.core.management import call_command

from coldfront.core import allocation
from coldfront.core.allocation.models import (
    AllocationAttributeChangeRequest,
    AllocationChangeRequest,
    AllocationChangeStatusChoice,
    AllocationAttribute
)
from coldfront.plugins.qumulo.tests.utils.mock_data import create_allocation, build_models

from coldfront.plugins.qumulo.services.allocation_service import AllocationService
from coldfront.plugins.qumulo.management.commands.deny_allocation_change_requests import Command

class TestDenyAllocationChangeRequests(TestCase):
    def setUp(self):
        build_data = build_models()

        self.project = build_data["project"]
        self.user = build_data["user"]

        self.form_data = {
            "project_pk": self.project.id,
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
            "service_rate": "consumption",
        }

        self.alloc = create_allocation(self.project, self.user, self.form_data)

        allocation_change_request = AllocationChangeRequest.objects.create(
                allocation=self.alloc,
                status=AllocationChangeStatusChoice.objects.get(name="Pending"),
                justification="updating",
                notes="updating",
                end_date_extension=10,
            )
        attribute = AllocationAttribute.objects.get(
            allocation=self.alloc,
            allocation_attribute_type__name="storage_ticket",
        )
        AllocationAttributeChangeRequest.objects.create(
                    allocation_attribute=attribute,
                    allocation_change_request=allocation_change_request,
                    new_value="ITSD-54322",
                )

    def test_denies_pending_allocation_change_requests(self):
        call_command("deny_allocation_change_requests")
        pending_requests = AllocationChangeRequest.objects.filter(status__name='Denied')
        self.assertEqual(1, pending_requests.count())

    def test_only_denies_pending_change_requests(self):
        AllocationChangeRequest.objects.create(
            allocation=self.alloc,
            status=AllocationChangeStatusChoice.objects.get(name="Approved"),
            justification="updating",
            notes="updating",
            end_date_extension=10,
        )
        call_command("deny_allocation_change_requests")
        denied_requests = AllocationChangeRequest.objects.filter(status__name='Denied')
        approved_requests = AllocationChangeRequest.objects.filter(status__name='Approved')
        self.assertEqual(1, denied_requests.count())
        self.assertEqual(1, approved_requests.count())