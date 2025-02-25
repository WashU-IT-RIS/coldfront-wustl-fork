import os
from io import StringIO

from django.test import TestCase
from unittest.mock import MagicMock

from coldfront.core.allocation.models import (
    Allocation,
    AllocationStatusChoice,
    AttributeType,
    AllocationAttributeType,
    AllocationLinkage,
)
from coldfront.plugins.qumulo.tests.utils.mock_data import (
    build_models,
    create_allocation,
)

from django.core.management import call_command

from coldfront.plugins.qumulo.management.commands.fix_add_allocation_attribute_billing_exempt import (
    Command,
)

STORAGE2_PATH = os.environ.get("STORAGE2_PATH")


class TestAddBillingExempt(TestCase):
    def setUp(self) -> None:
        build_data = build_models()

        self.project = build_data["project"]
        self.user = build_data["user"]

        return super().setUp()

    def test_invalid_default_value(self):
        out = StringIO()
        call_command(
            "fix_add_allocation_attribute_billing_exempt",
            "-d",
            "no",
            stdout=out,
        )
        self.assertIn("[Error] Invalid: ", out.getvalue())
        self.assertIn("Invalid Value", out.getvalue())

    def test_invalid_to_add_billing_exempt(self):
        out = StringIO()
        AllocationAttributeType.objects.update_or_create(
            name="exempt",
            defaults={
                "attribute_type": AttributeType.objects.get(name="Yes/No"),
                "is_required": True,
                "is_private": False,
                "is_changeable": False,
            },
        )
        call_command(
            "fix_add_allocation_attribute_billing_exempt",
            stdout=out,
        )
        self.assertIn("[Error] Invalid: ", out.getvalue())
        self.assertIn("Allocation Attribute Types conflict", out.getvalue())
        self.assertNotIn("Successfully added", out.getvalue())

    def test_successfully_added(self):
        out = StringIO()
        call_command(
            "fix_add_allocation_attribute_billing_exempt",
            stdout=out,
        )
        self.assertIn("[Info] Validation Pass", out.getvalue())
        self.assertIn("[Info] Successfully added billing_exempt", out.getvalue())

    def test_set_default_value(self):
        out = StringIO()
        call_command(
            "fix_add_allocation_attribute_billing_exempt",
            "--default_value",
            "Yes",
            stdout=out,
        )
        self.assertIn("[Info] Validation Pass", out.getvalue())
        self.assertIn("[Info] Successfully added billing_exempt", out.getvalue())
        self.assertNotIn("[Error] Failed to add", out.getvalue())
