from coldfront.core.user.models import User

from coldfront.core.project.models import Project, ProjectUser, ProjectUserRoleChoice


def grant_usersupport_global_project_manager():

    group_name = "RIS-UserSupport"
    projects = Project.objects.all()
    users = User.objects.filter(groups__name=group_name)
    for project in projects:
        for user in users:
            ProjectUser.objects.get_or_create(
                user=user, project=project, role=ProjectUserRoleChoice("Manager")
            )
