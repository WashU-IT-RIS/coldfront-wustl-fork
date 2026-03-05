from django.core.management import call_command

from django.test import TestCase

from io import StringIO

from coldfront.core.allocation.models import AllocationAttribute
from coldfront.plugins.qumulo.tests.fixtures import (
    create_metadata_for_testing,
)
from coldfront.plugins.qumulo.tests.helper_classes.factories import Storage2Factory


class CleanStorageExportPathTest(TestCase):

    def setUp(self):
        # Set up any necessary data for the tests
        create_metadata_for_testing()
        self.storage_allocations = []
        for _ in range(3):
            self.storage_allocations.append(Storage2Factory.create())

    def test_command_output_success(self):

        # Assert that no billing_cycle attributes exist before the command is run
        self.assertFalse(
            AllocationAttribute.objects.filter(
                allocation__in=self.storage_allocations,
                allocation_attribute_type__name="billing_cycle",
            ).exists()
        )
        out = StringIO()
        ids = [allocation.id for allocation in self.storage_allocations]
        call_command(
            "clean_billing_cycle",
            "--allocation-ids",
            ids,
            stdout=out,
        )
        # Assert that billing_cycle attributes have been created for the specified allocations
        self.assertTrue(
            AllocationAttribute.objects.filter(
                allocation__in=self.storage_allocations,
                allocation_attribute_type__name="billing_cycle",
            ).exists()
        )

        output = out.getvalue()
        self.assertIn(
            "Billing cycles have been created for the following allocations:",
            output,
        )

    def test_command_output_dry_run(self):

        # Assert that no billing_cycle attributes exist before the command is run
        self.assertFalse(
            AllocationAttribute.objects.filter(
                allocation__in=self.storage_allocations,
                allocation_attribute_type__name="billing_cycle",
            ).exists()
        )

        out = StringIO()
        ids = [allocation.id for allocation in self.storage_allocations]
        call_command(
            "clean_billing_cycle",
            "--allocation-ids",
            ids,
            "--dry-run",
            stdout=out,
        )
        # Assert that no billing_cycle attributes have been created
        self.assertFalse(
            AllocationAttribute.objects.filter(
                allocation__in=self.storage_allocations,
                allocation_attribute_type__name="billing_cycle",
            ).exists()
        )

        output = out.getvalue()
        self.assertIn(
            "Dry run enabled. Billing cycles would be created for the following allocations",
            output,
        )
        for allocation in self.storage_allocations:
            self.assertIn(
                f" - Allocation ID {allocation.id}: {allocation.status.name}",
                output,
            )
