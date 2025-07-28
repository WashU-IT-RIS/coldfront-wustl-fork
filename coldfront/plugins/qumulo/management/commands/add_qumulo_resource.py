from coldfront.core.resource.models import Resource, ResourceType
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("Adding Storage2/Qumulo resources")
        storage_resource_type = ResourceType.objects.get(name="Storage")
        acl_resource_type, created = ResourceType.objects.get_or_create(name="ACL")
        storage_resource_list = [
            {"name": "Storage2", "description": "Storage2 allocation via Qumulo"},
            {"name": "Storage3", "description": "Storage3 allocation via Qumulo"},
        ]

        for storage_resource in storage_resource_list:
            Resource.objects.get_or_create(
                resource_type=storage_resource_type,
                parent_resource=None,
                name=storage_resource["name"],
                description=storage_resource["description"],
                is_available=True,
                is_public=True,
                is_allocatable=True,
                requires_payment=True,
            )

        Resource.objects.get_or_create(
            name="rw",
            description="RW ACL",
            resource_type=acl_resource_type,
            is_available=True,
            is_public=False,
            is_allocatable=True,
            requires_payment=False,
        )

        Resource.objects.get_or_create(
            name="ro",
            description="RO ACL",
            resource_type=acl_resource_type,
            is_available=True,
            is_public=False,
            is_allocatable=True,
            requires_payment=False,
        )
