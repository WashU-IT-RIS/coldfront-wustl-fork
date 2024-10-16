from coldfront.core.project.models import ProjectAttributeType, AttributeType, Project, ProjectAttribute
from django.core.management.base import BaseCommand

from django.db.models import OuterRef, Subquery


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("Updating Qumulo Project Attributes")
        # updating required project attributes for all projects
        
        # for sponsor department number use "unknown"
        # can be updated manually later if necessary
        self._migrate_project_attribute("sponsor_department_number", "unknown")
        self._migrate_project_attribute("is_condo_group", "No")

        # no need to migrate quota_limit; that's only for condo_group projects
        # similarly, no need to migrate sla_name
    
    def _migrate_project_attribute(self, attribute_name, default_value):
        attribute_type = ProjectAttributeType.objects.get(name=attribute_name)
        attribute_sub_q = ProjectAttribute.objects.filter(
            project=OuterRef("pk"),
            proj_attr_type=attribute_type
        ).values("value")[:1]

        # find all projects
        all_projects = Project.objects.all()
        all_projects = all_projects.annotate(
            **{
                attribute_name: Subquery(attribute_sub_q)
            }
        )

        for project in all_projects:
            if getattr(project, attribute_name, None) is None:
                ProjectAttribute.objects.create(
                    proj_attr_type=attribute_type,
                    project=project,
                    value=default_value
                )

