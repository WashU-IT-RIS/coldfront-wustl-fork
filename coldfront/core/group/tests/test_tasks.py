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
        projectuser_status = ProjectUserStatusChoice.objects.get_or_create(
            name="Active"
        )[0]
        self.status_choice = project_status = ProjectStatusChoice.objects.get_or_create(
            name="Active"
        )[0]
        field_of_science = FieldOfScience.objects.get_or_create(description="Other")[0]

        # Create a group and three users
        self.group = Group.objects.get_or_create(name="RIS-UserSupport")[0]
        # Create two users as PIs
        self.user1 = User.objects.get_or_create(username="user1")[0]
        self.user2 = User.objects.get_or_create(username="user2")[0]
        # Create a user that is not a PI
        self.user3 = User.objects.get_or_create(username="user3")[0]

        # Add all users to the group
        for user in [self.user1, self.user2, self.user3]:
            user.groups.add(self.group)

        # Create two projects with separate PIs
        self.project1 = Project.objects.get_or_create(
            title="Project1",
            pi=self.user1,
            status=project_status,
            field_of_science=field_of_science,
        )[0]
        self.project2 = Project.objects.get_or_create(
            title="Project2",
            pi=self.user2,
            status=project_status,
            field_of_science=field_of_science,
        )[0]

        self.role_choice = ProjectUserRoleChoice.objects.get_or_create(name="Manager")[
            0
        ]

    # Test that the grant_usersupport_global_project_manager function works as expected
    def test_grant_usersupport_global_project_manager(self):
        grant_usersupport_global_project_manager()

        for project in [self.project1, self.project2]:
            for user in [self.user1, self.user2, self.user3]:
                project_user = ProjectUser.objects.get(project=project, user=user)
                self.assertEqual(project_user.role, self.role_choice)
                self.assertEqual(project_user.status, self.status_choice)
                self.assertTrue(project_user.enable_notifications)

    # Test that the function does not do anything if the group does not
    def test_no_group(self):
        self.group.delete()
        grant_usersupport_global_project_manager()
        self.assertFalse(ProjectUser.objects.exists())

    # Test that the function does not do anything if the role does not exist
    def test_no_role_choice(self):
        self.role_choice.delete()
        grant_usersupport_global_project_manager()
        self.assertFalse(ProjectUser.objects.exists())

    # Test that the function does not do anything if the status choice does not exist
    def test_no_status_choice(self):
        self.status_choice.delete()
        grant_usersupport_global_project_manager()
        self.assertFalse(ProjectUser.objects.exists())
