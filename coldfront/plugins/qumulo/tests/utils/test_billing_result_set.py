from django.test import TestCase, Client

from coldfront.plugins.qumulo.utils.billing_result_set import BillingResultSet
from coldfront.plugins.qumulo.tests.utils.mock_data import (
    build_models,
    create_allocation,
)
from coldfront.core.allocation.models import (
    AttributeType, AllocationAttributeType, AllocationStatusChoice, AllocationAttribute
)

class TestBillingResultSet(TestCase):
    def setUp(self):
        self.client = Client()
        build_data = build_models()

        self.project = build_data["project"]
        self.user = build_data["user"]

        self.default_form_data = {
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
            "service_rate": "general",
        }

        new_alloc = create_allocation(
            project=self.project,
            user=self.user,
            form_data=self.default_form_data
        )

        new_alloc.status = AllocationStatusChoice.objects.get(name="Active")
        new_alloc.end_date = "2025-06-30"
        new_alloc.start_date = "2025-03-01"
        new_alloc.save()
        subsidized_attribute = AllocationAttributeType.objects.get(
        name="subsidized"
        )
        AllocationAttribute.objects.create(
            allocation=new_alloc,
            allocation_attribute_type=subsidized_attribute,
            value="No",
        )

        out_of_date_alloc = create_allocation(
            project=self.project,
            user=self.user,
            form_data=self.default_form_data
        )

        out_of_date_alloc.status = AllocationStatusChoice.objects.get(name="Active")
        out_of_date_alloc.end_date = "2024-06-30"
        out_of_date_alloc.start_date = "2024-03-01"
        out_of_date_alloc.save()

        return super().setUp()



    def test_monthly(self):
        listl = BillingResultSet.retrieve_billing_result_set("monthly", "2025-04-30 00:00:00", "2025-06-01 00:00:00")
        count = len([l for l in listl if isinstance(l, dict)])
        expected_dict = {'billing_cycle': 'monthly', 'cost_center': 'Uncle Pennybags', 'subsidized': 'No', 'billing_exempt': 'No', 'pi': 'test', 'usage': 0.0}
        
        self.assertDictEqual(listl[0], expected_dict)
        self.assertEqual(count, 1)