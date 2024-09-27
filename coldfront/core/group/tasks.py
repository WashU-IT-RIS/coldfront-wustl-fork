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

    if not group:
        return

    all_projects = Project.objects.all()
    group_users = User.objects.filter(groups=group)
    role_choice = ProjectUserRoleChoice.objects.filter(name="Manager").first()
    status_choice = ProjectUserStatusChoice.objects.filter(name="Active").first()

    if not role_choice or not status_choice:
        return

    for project in all_projects:
        project_users = ProjectUser.objects.filter(
            project=project, user__in=group_users
        )
        existing_users = {pu.user_id: pu for pu in project_users}

        new_project_users = []
        updated_project_users = []
        for user in group_users:
            if user.id in existing_users:
                project_user = existing_users[user.id]
                project_user.role = role_choice
                project_user.status = status_choice
                project_user.enable_notifications = True
                # project_user.save()
                updated_project_users.append(project_user)
            else:
                new_project_users.append(
                    ProjectUser(
                        project=project,
                        user=user,
                        role=role_choice,
                        status=status_choice,
                        enable_notifications=True,
                    )
                )

        if updated_project_users:
            ProjectUser.objects.bulk_update(
                updated_project_users, ["role", "status", "enable_notifications"]
            )
        if new_project_users:
            ProjectUser.objects.bulk_create(new_project_users)
