from django.contrib.auth.models import Group
from coldfront.core.user.models import User
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

    # For each project, check if the user exists in the project
    for project in all_projects:
        for user in group_users:
            project_user = ProjectUser.objects.filter(
                project=project, user=user
            ).first()
            # If the user exists in the project, update the role, status, and enable_notifications
            if project_user:
                project_user.role = role_choice
                project_user.status = status_choice
                project_user.enable_notifications = True
                project_user.save()
            # If the user does not exist in the project, create a new ProjectUser
            else:
                project_user = ProjectUser.objects.create(
                    project=project,
                    user=user,
                    role=role_choice,
                    status=status_choice,
                    enable_notifications=True,
                )
