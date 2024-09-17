from coldfront.core.project.models import ProjectAttributeType, AttributeType, Project, ProjectAttribute
from django.core.management.base import BaseCommand

from django.db.models import OuterRef, Subquery


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("Updating Qumulo Project Attributes")
        # updating required project attributes for all projects
        
        # for sponsor department number use "unknown"
        # can be updated manually later if necessary
        dep_type = ProjectAttributeType.objects.get(name="sponsor_department_number")
        dep_sub_q = ProjectAttribute.objects.filter(
            project=OuterRef("pk"), 
            proj_attr_type=dep_type
        ).values("value")[:1]


        # find all projects
        all_projects = Project.objects.all()
        all_projects = all_projects.annotate(
            department_number=Subquery(dep_sub_q)
        )
        for project in all_projects:
            if project.department_number is None:
                ProjectAttribute.objects.create(
                    proj_attr_type=dep_type,
                    project=project,
                    value="Unknown"
                )
