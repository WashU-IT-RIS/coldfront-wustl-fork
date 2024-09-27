from django.test import TestCase
from django.contrib.auth.models import Group
from coldfront.core.user.models import User
from coldfront.core.group.tasks import grant_usersupport_global_project_manager

from coldfront.core.project.models import (
    Project,
    ProjectUser,
    ProjectUserRoleChoice,
    ProjectUserStatusChoice,
)


class GrantUserSupportGlobalProjectManagerTest(TestCase):
    def setUp(self):
        self.group = Group.objects.create(name="RIS-UserSupport")
        self.user1 = User.objects.create(username="user1")
        self.user2 = User.objects.create(username="user2")
        self.group.user_set.add(self.user1, self.user2)

        self.project1 = Project.objects.create(name="Project 1")
        self.project2 = Project.objects.create(name="Project 2")

        self.role_choice = ProjectUserRoleChoice.objects.create(name="Manager")
        self.status_choice = ProjectUserStatusChoice.objects.create(name="Active")

    def test_grant_usersupport_global_project_manager(self):
        grant_usersupport_global_project_manager()

        for project in [self.project1, self.project2]:
            for user in [self.user1, self.user2]:
                project_user = ProjectUser.objects.get(project=project, user=user)
                self.assertEqual(project_user.role, self.role_choice)
                self.assertEqual(project_user.status, self.status_choice)
                self.assertTrue(project_user.enable_notifications)

    def test_no_group(self):
        self.group.delete()
        grant_usersupport_global_project_manager()
        self.assertFalse(ProjectUser.objects.exists())

    def test_no_role_choice(self):
        self.role_choice.delete()
        grant_usersupport_global_project_manager()
        self.assertFalse(ProjectUser.objects.exists())

    def test_no_status_choice(self):
        self.status_choice.delete()
        grant_usersupport_global_project_manager()
        self.assertFalse(ProjectUser.objects.exists())
