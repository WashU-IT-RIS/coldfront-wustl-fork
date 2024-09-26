from coldfront.core.user.models import User

from coldfront.core.project.models import (
    Project,
    ProjectUser,
    ProjectUserRoleChoice,
    ProjectUserStatusChoice,
)


def grant_usersupport_global_project_manager():

    group_name = "RIS-UserSupport"
    all_projects = Project.objects.all()
    all_group_users = User.objects.filter(groups__name=group_name).all()
    manager_role = ProjectUserRoleChoice.objects.filter(name="Manager").first()
    user_status = ProjectUserStatusChoice.objects.filter(name="Active").first()

    for project in all_projects:
        print(f"Granting {group_name} users manager role on project {project}")
        for user in all_group_users:
            print(f"  - {user}")
            ProjectUser.objects.update_or_create(
                project=project,
                user=user,
                role=manager_role,
                status=user_status,
            )
