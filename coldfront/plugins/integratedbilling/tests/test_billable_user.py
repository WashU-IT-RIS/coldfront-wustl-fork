from django.test import TestCase

from coldfront.plugins.integratedbilling.factories import BillableUserFactory
from coldfront.plugins.integratedbilling.subsidies import BillableUser


class TestBillableUser(TestCase):
    def test_factory(self):
        # Create a BillableUser instance using the factory
        billable_user = BillableUserFactory()
        self.assertIsInstance(billable_user, BillableUser)
        self.assertIsNotNone(billable_user.get_user())

    def test_is_eligible_for_subsidy(self):
        # Create a BillableUser instance using the factory
        billable_user = BillableUserFactory()
        # Since the eligibility criteria is currently a placeholder, we expect this to return False
        self.assertFalse(billable_user.is_eligible_for_subsidy())

    def test_factory_by_allocation(self):
        # This test would require creating an Allocation instance and then using it to create a BillableUser
        # For now, we will just assert that the factory method exists and can be called without error
        from coldfront.core.billing.models import Allocation

        allocation = (
            Allocation()
        )  # This would need to be properly instantiated with required fields
        billable_user = BillableUser.factory_by_allocation(allocation)
        self.assertIsInstance(billable_user, BillableUser)

    def test_str_representation(self):
        billable_user = BillableUserFactory()
        str_representation = str(billable_user)
        self.assertTrue(str_representation.startswith("BillableUser(washu_key="))
