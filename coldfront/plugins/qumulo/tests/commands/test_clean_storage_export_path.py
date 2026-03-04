from django.core.management import call_command

from django.test import TestCase

from io import StringIO

from coldfront.core.allocation.models import AllocationAttribute
from coldfront.plugins.qumulo.tests.fixtures import (
    create_metadata_for_testing,
    create_ris_project_and_allocations_storage2,
)


class CleanStorageExportPathTest(TestCase):

    def setUp(self):
        # Set up any necessary data for the tests
        create_metadata_for_testing()
        self.storage_allocations = []
        for i in range(3):
            result = create_ris_project_and_allocations_storage2(
                storage_filesystem_path=f"/test/path{i}"
            )
            self.storage_allocations.append(result[1]["storage_allocation"])

    def test_command_output(self):

        out = StringIO()
        ids = [str(allocation.id) for allocation in self.storage_allocations]
        call_command(
            "clean_storage_export_path",
            "--allocation-ids",
            ids,
            stdout=out,
        )
        # Assertions
        values = AllocationAttribute.objects.filter(
            allocation__in=self.storage_allocations,
            allocation_attribute_type__name="storage_export_path",
        ).values_list("value", flat=True)
        self.assertTrue(all(value == "" for value in values))

        output = out.getvalue()
        self.assertIn(
            "Dry run enabled. The following storage_export_path would be cleaned:",
            output,
        )
