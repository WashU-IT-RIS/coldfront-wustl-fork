from coldfront.core.project.models import ProjectAttributeType, AttributeType
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("Adding Qumulo Project Attribute Types")
        # add a department_number at the project level that is *not* used for direct billing
        # could maybe have it default for Allocation?
        # NOTE - there is no UserAttributeType collection, so this is a more natural spot
        ProjectAttributeType.objects.update_or_create(
            name="sponsor_department_number",
            defaults={
                "attribute_type": AttributeType.objects.get(name="Text"),
                "is_required": False,
                "is_private": False,
                "is_unique": False,
                "is_changeable": True
            },
        )

        # NOTE: we'll keep "regular" allocations (even condo allocations) in "regular"
        # projects; a condo_group project is a special thing that lets us check the
        # sum of its allocations and bill them differently
        ProjectAttributeType.objects.update_or_create(
            name="is_condo_group",
            defaults= {
                "attribute_type": AttributeType.objects.get(name="Yes/No"),
                "is_required": True,
                "is_private": False,
                "is_unique": False,
                "is_changeable": True,
            },
        )

        ProjectAttributeType.objects.update_or_create(
            name="allow_nonfaculty",
            defaults={
                "attribute_type": AttributeType.objects.get(name="Yes/No"),
                "is_required": True,
                "is_private": False,
                "is_unique": False,
                "is_changeable": True,
            },
        )
