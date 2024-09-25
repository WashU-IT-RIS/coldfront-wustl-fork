from coldfront.core.user.models import User

from coldfront.core.project.models import Project, ProjectUser, ProjectUserRoleChoice


def grant_usersupport_global_project_manager():

    group_name = "RIS-UserSupport"
    all_projects = Project.objects.all()
    all_group_users = User.objects.filter(groups__name=group_name).all()
    manager_role = ProjectUserRoleChoice.objects.filter(name="Manager").first()

    for project in all_projects:
        for user in all_group_users:
            project_user = ProjectUser.objects.get_or_create(
                project=project, user=user, role=manager_role
            )
            project_user.save()
