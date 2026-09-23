import factory
from faker import Faker

fake = Faker()
from datetime import date
from django.test import TestCase
from coldfront.core.allocation.models import Allocation
from coldfront.core.project.models import Project
from coldfront.core.test_helpers.factories import AllocationStatusChoiceFactory
from coldfront.plugins.integratedbilling.factories import ServiceRateCategoryFactory
from coldfront.plugins.integratedbilling.models import ServiceRateCategory
from coldfront.plugins.qumulo.tests.fixtures import (
    create_metadata_for_testing,
    create_ris_project_and_allocations_storage2,
    create_ris_project_and_allocations_storage3,
)


class TestFixtures(TestCase):

    def setUp(self) -> None:
        create_metadata_for_testing()

        # Setup code to create test data if necessary
        self.current_active = ServiceRateCategoryFactory(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            archive_service=True,
        )
        self.current_archive = ServiceRateCategoryFactory(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            active_service=True,
        )
        self.previous_active = ServiceRateCategoryFactory(
            previous_service_rate=True, archive_service=True
        )
        self.previous_archive = ServiceRateCategoryFactory(
            previous_service_rate=True, active_service=True
        )

    def test_create_allocations_with_factory(self):
        self.results = []
        storage_path = Faker().file_path(depth=3)
        result = create_ris_project_and_allocations_storage2(
            storage_filesystem_path=storage_path,
            status=factory.SubFactory(AllocationStatusChoiceFactory, name="Pending"),
        )

        self.assertIsInstance(result["project"], Project)
        self.assertIsInstance(result["allocations"]["storage_allocation"], Allocation)
        self.assertIsInstance(result["allocations"]["rw_group"], Allocation)
        self.assertIsInstance(result["allocations"]["ro_group"], Allocation)
        self.assertEqual(result["allocations"]["storage_allocation"].status.name, "Pending")
        self.assertEqual(result["allocations"]["storage_allocation"].justification, "")
        self.assertEqual(result["allocations"]["storage_allocation"].project, result["project"])
        self.results.append(result)

        another_result = create_ris_project_and_allocations_storage3(
            storage_filesystem_path=storage_path,
            justification=Faker().sentence(),
        )
        self.assertIsInstance(another_result["project"], Project)
        self.assertIsInstance(another_result["allocations"]["storage_allocation"], Allocation)
        self.assertIsInstance(another_result["allocations"]["rw_group"], Allocation)
        self.assertIsInstance(another_result["allocations"]["ro_group"], Allocation)
        self.assertNotEqual(another_result["allocations"]["storage_allocation"].justification, "")
        print(f"Faker justification: {another_result['allocations']['storage_allocation'].justification}")


    def test_create_with_mocks(self):
        # Example of using mocks if needed
        pass

    def test_for_a_given_date_when_archive_comsuption_monthly_rate(self):
        usage_date = date(2025, 10, 1)
        model_name = "consumption"
        tier_name = "Archive"
        cycle = "monthly"

        categories = (
            ServiceRateCategory.rates.for_date(usage_date)
            .for_model(model_name)
            .for_tier(tier_name)
            .for_cycle(cycle)
        )

        self.assertEqual(categories.count(), 1)
        category = categories.get()
        self.assertEqual(category.model_name, model_name)
        self.assertEqual(category.tier_name, tier_name)
        self.assertEqual(category.cycle, cycle)
        self.assertGreaterEqual(usage_date, category.start_date)
        self.assertLessEqual(usage_date, category.end_date)
