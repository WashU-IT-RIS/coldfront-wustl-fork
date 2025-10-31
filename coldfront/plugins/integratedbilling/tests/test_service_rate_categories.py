from datetime import date
from django.test import TestCase
from coldfront.plugins.integratedbilling.factories import ServiceRateCategoryFactory
from coldfront.plugins.integratedbilling.models import ServiceRateCategory


class TestServiceRateCategories(TestCase):

    def setUp(self) -> None:
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

    def test_service_rate_category_retrieval(self):
        usage_date = date(2025, 10, 1)
        model_name = "consumption"
        tier_name = "archive"
        cycle = "monthly"

        categories = (
            ServiceRateCategory.rates.for_date(usage_date)
            .for_model(model_name)
            .for_tier(tier_name)
            .for_cycle(cycle)
        )

        self.assertEquals(categories.count(), 1)
        category = categories.get()
        self.assertEqual(category.model_name, model_name)
        self.assertEqual(category.tier_name, tier_name)
        self.assertEqual(category.cycle, cycle)
        self.assertGreaterEqual(usage_date, category.start_date)
        self.assertLessEqual(usage_date, category.end_date)

    def test_service_rate_category_no_match(self):
        usage_date = date(2025, 10, 1)
        model_name = "Nonexistent Model"
        tier_name = "archive"
        cycle = "monthly"

        categories = (
            ServiceRateCategory.rates.for_date(usage_date)
            .for_model(model_name)
            .for_tier(tier_name)
            .for_cycle(cycle)
        )
        self.assertEquals(categories.count(), 0)

    def test_service_rate_category_multiple_matches(self):
        usage_date = date(2024, 6, 15)
        model_name = "consumption"
        cycle = "monthly"

        categories = (
            ServiceRateCategory.rates.for_date(usage_date)
            .for_model(model_name)
            .for_cycle(cycle)
        )
        breakpoint()
        self.assertGreater(categories.count(), 0)  # Ensure at least one match exists
        for category in categories:
            assert category.model_name == model_name
            assert category.cycle == cycle
            assert category.start_date <= usage_date <= category.end_date

    def test_service_rate_category_edge_dates(self):
        model_name = "consumption"
        tier_name = "active"
        cycle = "monthly"

        # Test start date
        start_date = date(2025, 1, 1)
        categories_start = (
            ServiceRateCategory.rates.for_date(start_date)
            .for_model(model_name)
            .for_tier(tier_name)
            .for_cycle(cycle)
        )
        self.assertGreater(
            categories_start.count(), 0
        )  # Ensure at least one match exists
        for category in categories_start:
            self.assertTrue(category.start_date <= start_date <= category.end_date)

        # Test end date
        end_date = date(2025, 12, 31)
        categories_end = (
            ServiceRateCategory.rates.for_date(end_date)
            .for_model(model_name)
            .for_tier(tier_name)
            .for_cycle(cycle)
        )
        self.assertGreater(
            categories_end.count(), 0
        )  # Ensure at least one match exists
        for category in categories_end:
            self.assertTrue(category.start_date <= end_date <= category.end_date)

    def test_service_rate_category_invalid_date(self):
        usage_date = date(2025, 1, 1)  # Assuming no categories exist for this date
        model_name = "Standard Storage"
        tier_name = "Tier 1"
        cycle = "Monthly"

        categories = (
            ServiceRateCategory.rates.for_date(usage_date)
            .for_model(model_name)
            .for_tier(tier_name)
            .for_cycle(cycle)
        )

        assert categories.count() == 0  # Expecting no matches for invalid date
