from django.test import TestCase
from .models import ServiceRateCategory


class ServiceRateCategoryModelTest(TestCase):
    def setUp(self):
        self.category = ServiceRateCategory.objects.create(
            name="Test Category", description="A test service rate category"
        )

    def test_category_creation(self):
        self.assertEqual(self.category.name, "Test Category")
        self.assertEqual(self.category.description, "A test service rate category")
        self.assertIsInstance(self.category, ServiceRateCategory)

    def test_str_method(self):
        self.assertEqual(str(self.category), "Test Category")

    def test_category_update(self):
        self.category.description = "An updated description"
        self.category.save()
        updated_category = ServiceRateCategory.objects.get(id=self.category.id)
        self.assertEqual(updated_category.description, "An updated description")

    def test_category_deletion(self):
        category_id = self.category.id
        self.category.delete()
        with self.assertRaises(ServiceRateCategory.DoesNotExist):
            ServiceRateCategory.objects.get(id=category_id)

    def test_unique_name_constraint(self):
        with self.assertRaises(Exception):
            ServiceRateCategory.objects.create(
                name="Test Category", description="Another test service rate category"
            )

    def test_blank_name_validation(self):
        with self.assertRaises(Exception):
            ServiceRateCategory.objects.create(
                name="", description="A test service rate category with blank name"
            )

    def test_blank_description_validation(self):
        with self.assertRaises(Exception):
            ServiceRateCategory.objects.create(
                name="Another Test Category", description=""
            )

    def test_long_name_validation(self):
        long_name = "A" * 256  # Assuming max_length is 255
        with self.assertRaises(Exception):
            ServiceRateCategory.objects.create(
                name=long_name,
                description="A test service rate category with long name",
            )

    def test_long_description_validation(self):
        long_description = "D" * 256  # Assuming max_length is 255
        with self.assertRaises(Exception):
            ServiceRateCategory.objects.create(
                name="Long Description Category", description=long_description
            )

    def test_start_date_in_past(self):
        from datetime import date, timedelta

        past_date = date.today() - timedelta(days=1)
        with self.assertRaises(Exception):
            ServiceRateCategory.objects.create(
                name="Past Start Date Category",
                description="A test service rate category with past start date",
                start_date=past_date,
                end_date=date.today() + timedelta(days=10),
            )

    def test_end_date_before_start_date(self):
        from datetime import date, timedelta

        start_date = date.today() + timedelta(days=10)
        end_date = date.today() + timedelta(days=5)
        with self.assertRaises(Exception):
            ServiceRateCategory.objects.create(
                name="Invalid Date Range Category",
                description="A test service rate category with end date before start date",
                start_date=start_date,
                end_date=end_date,
            )

    def test_valid_date_range(self):
        from datetime import date, timedelta

        start_date = date.today() + timedelta(days=5)
        end_date = date.today() + timedelta(days=10)
        category = ServiceRateCategory.objects.create(
            name="Valid Date Range Category",
            description="A test service rate category with valid date range",
            start_date=start_date,
            end_date=end_date,
        )
        self.assertIsInstance(category, ServiceRateCategory)

    def test_default_manager(self):
        categories = ServiceRateCategory.objects.all()
        self.assertIn(self.category, categories)

    def test_current_manager(self):
        from datetime import date, timedelta

        start_date = date.today() - timedelta(days=5)
        end_date = date.today() + timedelta(days=5)
        current_category = ServiceRateCategory.objects.create(
            name="Current Category",
            description="A test service rate category that is current",
            start_date=start_date,
            end_date=end_date,
        )
        current_categories = ServiceRateCategory.current.all()
        self.assertIn(current_category, current_categories)
        self.assertNotIn(
            self.category, current_categories
        )  # Assuming self.category is not current

    def test_historical_records(self):
        initial_history_count = self.category.history.count()
        self.category.description = "Updated for history test"
        self.category.save()
        updated_history_count = self.category.history.count()
        self.assertEqual(updated_history_count, initial_history_count + 1)
        last_history = self.category.history.last()
        self.assertEqual(last_history.description, "Updated for history test")

    def test_history_str_method(self):
        history_entry = self.category.history.first()
        self.assertIn("Test Category", str(history_entry))

    def test_history_date_tracking(self):
        history_entry = self.category.history.first()
        self.assertIsNotNone(history_entry.history_date)

    def test_history_user_tracking(self):
        history_entry = self.category.history.first()
        self.assertIsNone(
            history_entry.history_user
        )  # Assuming no user is set during tests

    def test_history_type_tracking(self):
        history_entry = self.category.history.first()
        self.assertEqual(history_entry.history_type, "+")  # Creation should be "+"

    def test_multiple_history_entries(self):
        self.category.description = "First update"
        self.category.save()
        self.category.description = "Second update"
        self.category.save()
        history_entries = self.category.history.all()
        self.assertEqual(history_entries.count(), 3)  # Creation + 2 updates
        descriptions = [entry.description for entry in history_entries]
        self.assertIn("First update", descriptions)
        self.assertIn("Second update", descriptions)
