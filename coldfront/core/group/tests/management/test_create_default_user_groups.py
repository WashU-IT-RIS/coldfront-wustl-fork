from django.core.management import call_command
from django.test import TestCase
from django.contrib.auth.models import Group, Permission
from coldfront.core.group.management.commands.create_default_user_groups import (
    DEFAULT_RIS_USER_GROUPS,
)


class CreateDefaultUserGroupsTest(TestCase):
    def test_create_default_user_groups(self):
        # Ensure no groups exist before running the command
        self.assertEqual(Group.objects.count(), 0)

        # Call the management command
        call_command("create_default_user_groups")

        # Check that the groups were created
        for group in DEFAULT_RIS_USER_GROUPS:
            group_obj = Group.objects.get(name=group["name"])
            self.assertIsNotNone(group_obj)
            self.assertEqual(group_obj.permissions.count(), len(group["permissions"]))

            # Check that the permissions were added to the group
            for permission in group["permissions"]:
                perm_obj = Permission.objects.get(id=permission["id"])
                self.assertIn(perm_obj, group_obj.permissions.all())
