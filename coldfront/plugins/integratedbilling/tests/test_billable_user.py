from django.test import TestCase  

from coldfront.plugins.integratedbilling.subsidies import BillableUser
from coldfront.plugins.qumulo.tests.fixtures import create_ris_project_and_allocations_storage3


class TestBillableUser(TestCase):
    def setUp(self):
        # Set up any necessary test data or mocks here
        pass
    
    def test_factory(self):
        # Create a BillableUser instance using the factory
        billable_user = BillableUser.factory("testuser")
        self.assertIsInstance(billable_user, BillableUser)
        self.assertIsNotNone(billable_user.get_user())

    
    def test_is_eligible_for_subsidy(self):
        # Create a BillableUser instance using the factory
        billable_user = BillableUser.factory("testuser")
        self.assertFalse(billable_user.is_eligible_for_subsidy())  # Assuming testuser is not faculty

    
    def test_factory_by_allocation(self):
        # This test would require creating an Allocation instance and then using it to create a BillableUser
        _, allocations = create_ris_project_and_allocations_storage3(
            storage_filesystem_path="/storage3/fs1/testuser",
        )
        allocation = allocations["storage_allocation"]
        billable_user = BillableUser.factory_by_allocation(allocation)
        self.assertIsInstance(billable_user, BillableUser)

    
    def test_str_representation(self):
        billable_user = BillableUser()
        str_representation = str(billable_user)
        self.assertTrue(str_representation.startswith("BillableUser(washu_key="))
