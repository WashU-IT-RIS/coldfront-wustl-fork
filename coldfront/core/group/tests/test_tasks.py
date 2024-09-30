from django.test import TestCase
from django.contrib.auth.models import Group
from coldfront.core.user.models import User
from coldfront.core.group.tasks import grant_usersupport_global_project_manager

from coldfront.core.project.models import (
    Project,
    ProjectStatusChoice,
    ProjectUser,
    ProjectUserRoleChoice,
    ProjectUserStatusChoice,
    FieldOfScience,
)


class GrantUserSupportGlobalProjectManagerTest(TestCase):
    def setUp(self):
        self.projectuser_status, b = ProjectUserStatusChoice.objects.get_or_create(
            name="Active"
        )
        self.project_status, b = ProjectStatusChoice.objects.get_or_create(
            name="Active"
        )
        field_of_science, b = FieldOfScience.objects.get_or_create(description="Other")

        # Create a group and three users
        self.group, b = Group.objects.get_or_create(name="RIS-UserSupport")
        # Define user attributes
        user_attributes = [
            {"username": "user1"},
            {"username": "user2"},
            {"username": "user3"},
        ]
        # Create users and store them in an array
        self.users = []
        for attrs in user_attributes:
            user, b = User.objects.get_or_create(**attrs)
            self.users.append(user)
            # Add the user to the group
            self.users[user.username].groups.add(self.group)

        # Create two projects with separate PIs
        self.project1, b = Project.objects.get_or_create(
            title="Project1",
            pi=self.users[1],
            status=self.project_status,
            field_of_science=field_of_science,
        )
        self.project2, b = Project.objects.get_or_create(
            title="Project2",
            pi=self.users[2],
            status=self.project_status,
            field_of_science=field_of_science,
        )

        self.projectuser_role, b = ProjectUserRoleChoice.objects.get_or_create(
            name="Manager"
        )

    # Test that the grant_usersupport_global_project_manager function works as expected
    def test_grant_usersupport_global_project_manager(self):
        grant_usersupport_global_project_manager()

        for project in [self.project1, self.project2]:
            for user in self.users:
                project_user = ProjectUser.objects.get(project=project, user=user)
                self.assertEqual(project_user.role, self.projectuser_role)
                self.assertEqual(project_user.status, self.projectuser_status)
                self.assertTrue(project_user.enable_notifications)

    # Test that the function does not do anything if the group does not
    def test_no_group(self):
        self.group.delete()
        grant_usersupport_global_project_manager()
        self.assertFalse(ProjectUser.objects.exists())

    # Test that the function does not do anything if the role does not exist
    def test_no_projectuser_role(self):
        self.projectuser_role.delete()
        grant_usersupport_global_project_manager()
        self.assertFalse(ProjectUser.objects.exists())

    # Test that the function does not do anything if the status choice does not exist
    def test_no_projectuser_status(self):
        self.projectuser_status.delete()
        grant_usersupport_global_project_manager()
        self.assertFalse(ProjectUser.objects.exists())
