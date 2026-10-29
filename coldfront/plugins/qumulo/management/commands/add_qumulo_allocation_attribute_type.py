from coldfront.core.allocation.models import AllocationAttributeType, AttributeType
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("Adding Qumulo Allocation Attribute Types")
        AllocationAttributeType.objects.update_or_create(
            name="storage_name",
            defaults={
                "attribute_type": AttributeType.objects.get(name="Text"),
                "is_required": True,
                "is_private": False,
                "is_unique": True,
                "is_changeable": False,
            }
        )

        AllocationAttributeType.objects.update_or_create(
            name="storage_quota",
            defaults={
                "attribute_type": AttributeType.objects.get(name="Int"),
                "has_usage": True,
                "is_required": True,
                "is_private": False,
                "is_unique": True,
                "is_changeable": True,
            }
        )

        AllocationAttributeType.objects.update_or_create(
            name="storage_protocols",
            defaults={
                "attribute_type": AttributeType.objects.get(name="Text"),
                "is_required": True,
                "is_private": False,
                "is_changeable": True,
                "is_unique": True,
            }
        )

        AllocationAttributeType.objects.update_or_create(
            name="storage_filesystem_path",
            defaults={
                "attribute_type": AttributeType.objects.get(name="Text"),
                "is_required": True,
                "is_private": False,
                "is_unique": True,
                "is_changeable": False,
            }
        )

        AllocationAttributeType.objects.update_or_create(
            name="storage_ticket",
            defaults={
                "attribute_type": AttributeType.objects.get(name="Text"),
                "is_required": False,
                "is_private": False,
                "is_unique": False,
                "is_changeable": False,
            }
        )

        AllocationAttributeType.objects.update_or_create(
            name="storage_export_path",
            defaults={
                "attribute_type": AttributeType.objects.get(name="Text"),
                "is_required": True,
                "is_private": False,
                "is_unique": True,
                "is_changeable": False,
            }
        )

        AllocationAttributeType.objects.update_or_create(
            name="storage_acl_name",
            defaults={
                "attribute_type": AttributeType.objects.get(name="Text"),
                "is_required": True,
                "is_private": True,
                "is_unique": True,
                "is_changeable": False,
            }
        )

        AllocationAttributeType.objects.update_or_create(
            name="storage_allocation_pk",
            defaults={
                "attribute_type": AttributeType.objects.get(name="Int"),
                "is_required": True,
                "is_private": True,
                "is_unique": True,
                "is_changeable": False,
            }
        )

        AllocationAttributeType.objects.update_or_create(
            attribute_type=AttributeType.objects.get(name="Text"),
            name="cost_center",
            defaults={
                "is_required": True,
                "is_private": False,
                "is_unique": True,
                "is_changeable": False,
            }
        )

        AllocationAttributeType.objects.update_or_create(
            name="department_number",
            defaults={
                "attribute_type": AttributeType.objects.get(name="Text"),
                "is_required": True,
                "is_private": False,
                "is_unique": True,
                "is_changeable": False,
            }
        )

        AllocationAttributeType.objects.update_or_create(
            name="department_name",
            defaults={
                "attribute_type": AttributeType.objects.get(name="Text"),
                "is_required": True,
                "is_private": False,
                "is_unique": True,
                "is_changeable": False,
            }
        )

        AllocationAttributeType.objects.update_or_create(
            name="technical_contact",
            defaults={
                "attribute_type": AttributeType.objects.get(name="Text"),
                "is_required": False,
                "is_private": False,
                "is_unique": True,
                "is_changeable": True,
            }
        )

        AllocationAttributeType.objects.update_or_create(
            name="billing_contact",
            defaults={
                "attribute_type": AttributeType.objects.get(name="Text"),
                "is_required": False,
                "is_private": False,
                "is_unique": True,
                "is_changeable": True,
            }
        )

        AllocationAttributeType.objects.filter(name="service_rate").update(
            name="service_rate_category"
        )

        AllocationAttributeType.objects.update_or_create(
            name="service_rate_category",
            defaults={
                "attribute_type": AttributeType.objects.get(name="Text"),
                "is_required": True,
                "is_private": False,
                "is_changeable": True,
                "is_unique": False,
            },
        )

        # these are the fields that will be migrated from Storage1
        AllocationAttributeType.objects.update_or_create(
            name="secure",
            defaults={
                "attribute_type": AttributeType.objects.get(name="Yes/No"),
                "is_required": True,
                "is_private": False,
                "is_changeable": False,
            }
        )

        # indicates whether the allocation is subject to being audited
        AllocationAttributeType.objects.update_or_create(
            name="audit",
            defaults={
                "attribute_type": AttributeType.objects.get(name="Yes/No"),
                "is_required": True,
                "is_private": False,
                "is_changeable": False,
            }
        )

        AllocationAttributeType.objects.update_or_create(
            name="prepaid_billing_date",
            defaults={
                "attribute_type": AttributeType.objects.get(name="Date"),
                "is_required": False,
                "is_private": False,
                "is_changeable": True,
            }
        )

        AllocationAttributeType.objects.update_or_create(
            name="billing_startdate",
            defaults={
                "attribute_type": AttributeType.objects.get(name="Date"),
                "is_required": False,
                "is_private": False,
                "is_changeable": False,
            },
        )

        AllocationAttributeType.objects.update_or_create(
            name="fileset_name",
            defaults={
                "attribute_type": AttributeType.objects.get(name="Text"),
                "is_required": False,
                "is_private": False,
                "is_changeable": False,
            },
        )

        AllocationAttributeType.objects.update_or_create(
            name="fileset_alias",
            defaults={
                "attribute_type": AttributeType.objects.get(name="Text"),
                "is_required": False,
                "is_private": False,
                "is_changeable": False,
            },
        )

        AllocationAttributeType.objects.filter(name="exempt").update(
            name="billing_exempt",
        )

        AllocationAttributeType.objects.update_or_create(
            name="billing_exempt",
            defaults={
                "attribute_type": AttributeType.objects.get(name="Yes/No"),
                "is_required": True,
                "is_private": False,
                "is_changeable": True,
                "is_unique": False,
            },
        )

        AllocationAttributeType.objects.update_or_create(
            name="itsm_comment",
            defaults={
                "attribute_type": AttributeType.objects.get(name="JSON"),
                "is_required": False,
                "is_private": False,
                "is_changeable": False,
            }
        )

        AllocationAttributeType.objects.update_or_create(
            name="subsidized",
            defaults={
                "attribute_type": AttributeType.objects.get(name="Yes/No"),
                "is_required": True,
                "is_private": False,
                "is_changeable": False,
            }
        )

        AllocationAttributeType.objects.update_or_create(
            name="billing_cycle",
            defaults={
                "attribute_type": AttributeType.objects.get(name="Text"),
                "is_required": True,
                "is_private": False,
                "is_changeable": True,
            }
        )

        AllocationAttributeType.objects.update_or_create(
            name="prepaid_time",
            defaults={
                "attribute_type": AttributeType.objects.get(name="Int"),
                "is_required": False,
                "is_private": False,
                "is_changeable": True,
            }
        )

        AllocationAttributeType.objects.update_or_create(
            name="sla_name",
            defaults={
                "attribute_type": AttributeType.objects.get(name="Text"),
                "is_required": False,
                "is_private": False,
                "is_unique": False,
                "is_changeable": True,
            }
        )

        AllocationAttributeType.objects.update_or_create(
            name="prepaid_expiration",
            defaults={
                "attribute_type": AttributeType.objects.get(name="Date"),
                "is_required": False,
                "is_private": False,
                "is_unique": False,
                "is_changeable": False,
            }
        )
