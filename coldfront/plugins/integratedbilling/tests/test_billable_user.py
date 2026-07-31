from unittest import mock
from django.test import TestCase
from typing import Optional

from coldfront.core.test_helpers.factories import UserFactory
from coldfront.plugins.integratedbilling.subsidies import (
    BillableUser,
    is_eligible_for_subsidy,
)
from coldfront.plugins.qumulo.tests.fixtures import create_metadata_for_testing
from coldfront.plugins.qumulo.tests.helper_classes.factories import (
    RisProjectFactory,
    Storage2Factory,
)


I_AM_A_FRIEND = "i-am-a-friend"
I_AM_AN_ALUMNI = "i-am-an-alumni"
UNKNOWN_USER = "unknown-user"


def is_faculty_member_side_effect(washu_key: str) -> bool:
    if washu_key == I_AM_A_FRIEND:
        return False

    if washu_key == I_AM_AN_ALUMNI:
        return False

    if washu_key == UNKNOWN_USER:
        raise ValueError("Cannot determine the user's eligibility for subsidy")

    return True


class TestBillableUser(TestCase):

    def setUp(self):
        create_metadata_for_testing()

        # faculty user for testing
        self.storage_allocation = (
            Storage2Factory()
        )  # Create a test allocation with a sponsor PI
        self.pi = self.storage_allocation.project.pi

        # non faculty users for testing
        for washu_key in [I_AM_A_FRIEND, I_AM_AN_ALUMNI, UNKNOWN_USER]:
            pi = UserFactory(username=washu_key)
            project = RisProjectFactory(pi=pi)
            Storage2Factory(project=project)

    def test_factory(self):
        # Create a BillableUser instance using the factory
        billable_user = BillableUser.factory_by_allocation(self.storage_allocation)
        self.assertIsInstance(billable_user, BillableUser)
        self.assertIsNotNone(billable_user.get_user())

    @mock.patch("coldfront.plugins.integratedbilling.subsidies.ActiveDirectoryAPI")
    def test_is_eligible_for_subsidy(self, mock_active_directory_api):
        mock_active_directory_api.return_value.is_faculty_member.side_effect = (
            is_faculty_member_side_effect
        )

        # context when the user is faculty, the user is eligible for subsidy
        username = self.pi.username
        self.assertTrue(is_eligible_for_subsidy(username))

        # context when the user is a friend or an alumni, the user is not eligible for subsidy
        for washu_key in [I_AM_A_FRIEND, I_AM_AN_ALUMNI]:
            self.assertFalse(is_eligible_for_subsidy(washu_key))

    def test_factory_by_allocation(self):
        # This test would require creating an Allocation instance and then using it to create a BillableUser
        billable_user = BillableUser.factory_by_allocation(self.storage_allocation)
        self.assertIsInstance(billable_user, BillableUser)

    def test_str_representation(self):
        user = self.pi  # Use the PI from the allocation as the test user
        billable_user = BillableUser(user.username)
        str_representation = str(billable_user)
        self.assertTrue(
            str_representation.startswith(f"BillableUser(washu_key={user.username})")
        )

    def test_get_user(self):
        user = self.pi  # Use the PI from the allocation as the test user
        billable_user = BillableUser(user.username)
        retrieved_user = billable_user.get_user()
        self.assertEqual(retrieved_user, user)


    def test_unknown_user_raises_value_error(self):
        with self.assertRaises(ValueError) as context:
            is_eligible_for_subsidy(UNKNOWN_USER)
        self.assertIn("Cannot determine the user's eligibility for subsidy", str(context.exception))


# def ad_lookup_get_user_side_effect(washu_key: str, search_base: Optional[str] = None, attributes: Optional[list[str]] = ["wustlEduPrimaryRole"]) -> dict:
#     if washu_key == I_AM_A_FRIEND:
#         return {"sAMAccountName": I_AM_A_FRIEND, "attributes": {attributes[0]: "FRIEND"}}

#     if washu_key == I_AM_AN_ALUMNI:
#         return {"sAMAccountName": I_AM_AN_ALUMNI, "attributes": {attributes[0]: "ALUMNI"}}

#     return {"sAMAccountName": washu_key, "attributes": {attributes[0]: "FACULTY"}}
