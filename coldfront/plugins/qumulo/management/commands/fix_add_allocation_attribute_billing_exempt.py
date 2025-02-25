"""
    This is a patch.
    The assumption is the allocation_attribute_type has been created.
    This is to add the required allocation_attribute to each allocations
        if the allocation doesn't have the allocation_attibute.
    This is re-runable in production.
    This is designed only for billing_exempt with its default value, "No".

    1. Confirm there is no concurrent existence of exempt and billing_exempt
        in the allocation_attribute_type table.
    2. Confirm billing_exempt is an allocation_attribute_type in Coldfront.

        If both exempt and billing_exempt are exist, 
            Prompt for a system error. Require AppEng to intervene for resolution:
                Copy the value of allocation_attirbute exempt to billing_exempt for all allocations
                Delete the allocation_attribute exempt for all allocations
            Fail and report error.
        Else If billing_exempt not exist,
            Prompt to run coldfront command "add_qumulo_allocation_attribute_type"
            Exit

    3. Loop to each allocation and
        set billing_exempt to default "No" if there is no such allocation_attribute. 
"""

import sys
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.management.base import BaseCommand, CommandError
from coldfront.core.utils.validate import AttributeValidator
from coldfront.core.allocation.models import (
    AllocationAttributeType,
    Allocation,
    AllocationAttribute,
)


class Command(BaseCommand):
    help = """
        Run this command will ensure the required allocation attribute billing_exempt in each allocations.
        The default values are "Yes" or "No", and case-sensitive.
    """

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "-d",
            "--default_value",
            default="No",
            type=str,
            help="modify the default value of billing_exempt",
        )

    def _validate_adding_billing_exempt(self):
        has_billing_exempt = False
        has_exempt = False

        try:
            AllocationAttributeType.objects.get(name="billing_exempt")
            has_billing_exempt = True
            AllocationAttributeType.objects.get(name="exempt")
            has_exempt = True
            if has_billing_exempt and has_exempt:
                raise ValidationError(
                    self.style.ERROR(
                        """
                        Allocation Attribute Types conflict: Require AppEng to migrate exempt to billing_exempt
                            1. Copy the value of allocation_attirbute exempt to billing_exempt for all allocations
                            2. Delete the allocation_attribute exempt for all allocations
                        """
                    )
                )

        except ObjectDoesNotExist:
            if not has_billing_exempt:
                raise Exception(
                    self.style.WARNING(
                        "Warning: Allocation Attribute Type missing: Run coldfront command 'add_qumulo_allocation_attribute_type'."
                    )
                )
            else:  # not has_exempt:
                self.stdout.write(
                    self.style.SUCCESS(
                        "[Info] Validation Pass: The system is ready for adding billing_exempt to pre-existing allocations."
                    )
                )

    def _add_billing_exempt(self):
        alloc_attr_type = AllocationAttributeType.objects.get(name="billing_exempt")
        allocations = Allocation.objects.filter(resources__name="Storage2")
        for allocation in allocations:
            try:
                AllocationAttribute.objects.get(
                    allocation_attribute_type=alloc_attr_type,
                    allocation=allocation,
                )
            except ObjectDoesNotExist:
                allocation_attribute = AllocationAttribute(
                    allocation_attribute_type=alloc_attr_type,
                    allocation=allocation,
                    value=self.default_value,
                )
                allocation_attribute.save()
                self.counter += 1
            except Exception as e:
                raise CommandError(
                    self.style.ERROR(f"[Error] Failed to add billing_exempt: {e}")
                )

    def handle(self, *args, **options) -> None:
        self.default_value = options["default_value"]
        self.counter = 0

        attr_validator = AttributeValidator(self.default_value)
        try:
            attr_validator.validate_yes_no()
            self._validate_adding_billing_exempt()
            self._add_billing_exempt()
            self.stdout.write(
                self.style.SUCCESS(
                    f"[Info] Successfully added {self.counter} billing_exempt as an allocation attribute to pre-existing allocations."
                )
            )
        except CommandError as e:
            self.stdout.write(self.style.ERROR(f"[Error] Failed: {e}"))
        except ValidationError as e:
            self.stdout.write(self.style.ERROR(f"[Error] Invalid: {e}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"[Error] {e}"))
