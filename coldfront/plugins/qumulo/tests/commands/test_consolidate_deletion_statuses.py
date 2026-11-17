from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from coldfront.core.allocation.models import Allocation, AllocationStatusChoice
from coldfront.core.test_helpers.factories import AllocationStatusChoiceFactory
from coldfront.plugins.qumulo.tests.fixtures import (
    create_metadata_for_testing,
    create_ris_project_and_allocations_storage2,
)


class ConsolidateDeletionStatusesCommandTest(TestCase):
    def setUp(self):
        create_metadata_for_testing()
        self.legacy_status = AllocationStatusChoiceFactory(name="Ready for Deletion")
        self.correct_status = AllocationStatusChoiceFactory(name="Ready for deletion")
        self.unrelated_status = AllocationStatusChoiceFactory(name="Deleted")
        self.legacy_allocations = []
        for index in range(2):
            _, allocations = create_ris_project_and_allocations_storage2(
                storage_filesystem_path=f"/tmp/legacy-{index}"
            )
            allocation = allocations["storage_allocation"]
            allocation.status = self.legacy_status
            allocation.save(update_fields=["status"])
            self.legacy_allocations.append(allocation)

        _, allocations = create_ris_project_and_allocations_storage2(
            storage_filesystem_path="/tmp/correct"
        )
        self.correct_allocation = allocations["storage_allocation"]
        self.correct_allocation.status = self.correct_status
        self.correct_allocation.save(update_fields=["status"])

        _, allocations = create_ris_project_and_allocations_storage2(
            storage_filesystem_path="/tmp/unrelated"
        )
        self.unrelated_allocation = allocations["storage_allocation"]
        self.unrelated_allocation.status = self.unrelated_status
        self.unrelated_allocation.save(update_fields=["status"])

    def test_updates_matching_allocations_to_canonical_name(self):
        out = StringIO()
        call_command("consolidate_deletion_statuses", stdout=out)

        self.assertEqual(Allocation.objects.filter(status__name="Ready for Deletion").count(), 0)
        self.assertEqual(Allocation.objects.filter(status__name="Ready for deletion").count(), 3)
        self.assertEqual(Allocation.objects.filter(status__name="Deleted").count(), 1)
        self.assertEqual(
            AllocationStatusChoice.objects.get(name="Ready for Deletion").pk,
            self.legacy_status.pk,
        )
        self.assertEqual(
            AllocationStatusChoice.objects.filter(name="Ready for deletion").count(), 1
        )
        self.assertEqual(
            AllocationStatusChoice.objects.get(name="Ready for deletion").pk,
            self.correct_status.pk,
        )

        self.assertIn(
            "Updated 2 allocation(s) from 'Ready for Deletion' to 'Ready for deletion'.",
            out.getvalue(),
        )

    def test_keeps_unused_legacy_status_choice(self):
        for allocation in self.legacy_allocations:
            allocation.status = self.correct_status
            allocation.save(update_fields=["status"])

        out = StringIO()
        call_command("consolidate_deletion_statuses", stdout=out)

        self.assertEqual(Allocation.objects.filter(status__name="Ready for Deletion").count(), 0)
        self.assertEqual(Allocation.objects.filter(status__name="Ready for deletion").count(), 3)
        self.assertEqual(Allocation.objects.filter(status__name="Deleted").count(), 1)
        self.assertEqual(
            AllocationStatusChoice.objects.get(name="Ready for Deletion").pk,
            self.legacy_status.pk,
        )
        self.assertIn(
            "Updated 0 allocation(s) from 'Ready for Deletion' to 'Ready for deletion'.",
            out.getvalue(),
        )

