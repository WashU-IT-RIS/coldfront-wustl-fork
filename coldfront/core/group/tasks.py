from coldfront.core.user.models import User
from django.contrib.auth.models import Group

from coldfront.core.project.models import (
    Project,
    ProjectUser,
    ProjectUserRoleChoice,
    ProjectUserStatusChoice,
)


def grant_usersupport_global_project_manager() -> None:

    group_name = "RIS-UserSupport"
    group = Group.objects.filter(name=group_name).first()

    all_projects = Project.objects.all()
    group_users = User.objects.filter(groups=group)
    role_choice = ProjectUserRoleChoice.objects.filter(name="Manager").first()
    status_choice = ProjectUserStatusChoice.objects.filter(name="Active").first()

    for project in all_projects:
        for user in group_users:
            project_user = ProjectUser.objects.filter(
                project=project, user=user
            ).first()
            if project_user:
                print(f"Updating existing ProjectUser {user} for {project}")
                print(f"Role: old {project_user.role} new {role_choice}")
                print(f"Status: old {project_user.status} new {status_choice}")
                project_user.role = role_choice
                project_user.status = status_choice
                project_user.save()
            else:
                print(f"Creating ProjectUser {user} for {project}")
                project_user = ProjectUser.objects.create(
                    project=project, user=user, role=role_choice, status=status_choice
                )
                print(f"Created new ProjectUser {project_user}")
