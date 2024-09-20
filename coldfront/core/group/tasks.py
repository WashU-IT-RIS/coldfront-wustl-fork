from coldfront.core.user.models import User

from coldfront.core.project.models import Project, ProjectUser, ProjectUserRoleChoice


def grant_group_users_all_projects_manager(group_name: str):

    projects = Project.objects.all()
    users = User.objects.filter(groups__name=group_name)
    for project in projects:
        for user in users:
            ProjectUser.objects.get_or_create(
                user=user, project=project, role=ProjectUserRoleChoice("Manager")
            )
