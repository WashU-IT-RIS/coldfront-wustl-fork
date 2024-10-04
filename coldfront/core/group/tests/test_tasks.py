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
        self.projectuser_status, _ = ProjectUserStatusChoice.objects.get_or_create(
            name="Active"
        )
        self.project_status, _ = ProjectStatusChoice.objects.get_or_create(
            name="Active"
        )
        field_of_science, _ = FieldOfScience.objects.get_or_create(description="Other")

        # Create a group and three users
        self.group, _ = Group.objects.get_or_create(name="RIS-UserSupport")
        # Define user attributes
        user_attributes = [
            {"username": "user1"},
            {"username": "user2"},
            {"username": "user3"},
        ]
        # Create users and store them in an array
        self.users = []
        for attrs in user_attributes:
            user, _ = User.objects.get_or_create(**attrs)
            self.users.append(user)
            # Add the user to the group
            index = self.users.index(user)
            self.users[index].groups.add(self.group)

        # Create two projects with separate PIs
        self.project1, _ = Project.objects.get_or_create(
            title="Project1",
            pi=self.users[1],
            status=self.project_status,
            field_of_science=field_of_science,
        )
        self.project2, _ = Project.objects.get_or_create(
            title="Project2",
            pi=self.users[2],
            status=self.project_status,
            field_of_science=field_of_science,
        )

        self.projectuser_role, _ = ProjectUserRoleChoice.objects.get_or_create(
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
