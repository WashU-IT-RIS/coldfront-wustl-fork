from coldfront.core.allocation.models import AllocationAttributeType, AttributeType
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        # jprew - NOTE - adding new flags to these get_or_create
        # calls results in the creation of *new* AllocationAttributeType objects
        # which will lead to errors when finding them by name

        print("Adding Qumulo Allocation Attribute Types")
        AllocationAttributeType.objects.get_or_create(
            attribute_type=AttributeType.objects.get(name="Text"),
            name="storage_name",
            is_required=True,
            is_private=False,
            is_unique=True,
            is_changeable=False,
        )

        AllocationAttributeType.objects.get_or_create(
            attribute_type=AttributeType.objects.get(name="Int"),
            name="storage_quota",
            has_usage=True,
            is_required=True,
            is_private=False,
            is_unique=True,
            is_changeable=True,
        )

        AllocationAttributeType.objects.get_or_create(
            attribute_type=AttributeType.objects.get(name="Text"),
            name="storage_protocols",
            is_required=True,
            is_private=False,
            is_changeable=True,
            is_unique=True,
        )

        AllocationAttributeType.objects.get_or_create(
            attribute_type=AttributeType.objects.get(name="Text"),
            name="storage_filesystem_path",
            is_required=True,
            is_private=False,
            is_unique=True,
            is_changeable=False,
        )

        AllocationAttributeType.objects.get_or_create(
            attribute_type=AttributeType.objects.get(name="Text"),
            name="storage_ticket",
            is_required=False,
            is_private=False,
            is_unique=False,
            is_changeable=False,
        )

        AllocationAttributeType.objects.get_or_create(
            attribute_type=AttributeType.objects.get(name="Text"),
            name="storage_export_path",
            is_required=True,
            is_private=False,
            is_unique=True,
            is_changeable=False,
        )

        AllocationAttributeType.objects.get_or_create(
            attribute_type=AttributeType.objects.get(name="Text"),
            name="storage_acl_name",
            is_required=True,
            is_private=True,
            is_unique=True,
            is_changeable=False,
        )

        AllocationAttributeType.objects.get_or_create(
            attribute_type=AttributeType.objects.get(name="Int"),
            name="storage_allocation_pk",
            is_required=True,
            is_private=True,
            is_unique=True,
            is_changeable=False,
        )

        AllocationAttributeType.objects.get_or_create(
            attribute_type=AttributeType.objects.get(name="Text"),
            name="cost_center",
            is_required=True,
            is_private=False,
            is_unique=True,
            is_changeable=False,
        )

        AllocationAttributeType.objects.get_or_create(
            attribute_type=AttributeType.objects.get(name="Text"),
            name="department_number",
            is_required=True,
            is_private=False,
            is_unique=True,
            is_changeable=False,
        )

        AllocationAttributeType.objects.get_or_create(
            attribute_type=AttributeType.objects.get(name="Text"),
            name="technical_contact",
            is_required=False,
            is_private=False,
            is_unique=True,
            is_changeable=True,
        )

        AllocationAttributeType.objects.get_or_create(
            attribute_type=AttributeType.objects.get(name="Text"),
            name="billing_contact",
            is_required=False,
            is_private=False,
            is_unique=True,
            is_changeable=True,
        )

        AllocationAttributeType.objects.get_or_create(
            attribute_type=AttributeType.objects.get(name="Text"),
            name="service_rate",
            is_required=True,
            is_private=False,
            is_changeable=True,
            is_unique=False,
        )
