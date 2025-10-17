import datetime
from django.test import TestCase
from .factories import AllocationUsageFactory
from coldfront.core.billing.models import AllocationUsage

class AllocationUsageModelTest(TestCase):
    def test_allocation_usage_factory_creates_valid_instance(self):
        usage = AllocationUsageFactory()
        self.assertIsInstance(usage, AllocationUsage)
        self.assertTrue(isinstance(usage.external_key, int))
        self.assertTrue(isinstance(usage.source, str))
        self.assertTrue(isinstance(usage.sponsor_pi, str))
        self.assertTrue(isinstance(usage.billing_contact, str))
        self.assertTrue(isinstance(usage.fileset_name, str))
        self.assertTrue(isinstance(usage.service_rate_category, str))
        self.assertTrue(isinstance(usage.usage_tb, str))
        self.assertTrue(isinstance(usage.funding_number, str))
        self.assertTrue(isinstance(usage.exempt, bool))
        self.assertTrue(isinstance(usage.subsidized, bool))
        self.assertTrue(isinstance(usage.is_condo_group, bool))
        self.assertTrue(isinstance(usage.parent_id_key, int))
        self.assertTrue(isinstance(usage.quota, str))
        self.assertTrue(isinstance(usage.billing_cycle, str))
        self.assertTrue(hasattr(usage, 'usage_date'))
        self.assertTrue(isinstance(usage.storage_cluster, str))

    def test_allocation_usage_str_fields_not_empty(self):
        usage = AllocationUsageFactory()
        self.assertNotEqual(usage.source, "")
        self.assertNotEqual(usage.sponsor_pi, "")
        self.assertNotEqual(usage.billing_contact, "")
        self.assertNotEqual(usage.fileset_name, "")
        self.assertNotEqual(usage.service_rate_category, "")
        self.assertNotEqual(usage.usage_tb, "")
        self.assertNotEqual(usage.funding_number, "")
        self.assertNotEqual(usage.quota, "")
        self.assertNotEqual(usage.billing_cycle, "")
        self.assertNotEqual(usage.storage_cluster, "")


class AllocationUsageQuerySetTest(TestCase):
    def setUp(self):
        self.usage_date = datetime.date(2024, 6, 1)
        self.pi1 = "pi1"
        self.pi2 = "pi2"
        self.fileset1 = "filesetA"
        self.fileset2 = "filesetB"
        self.fileset3 = "filesetC"
        # Create various AllocationUsage instances
        self.alloc1 = AllocationUsageFactory(
            usage_date=self.usage_date,
            exempt=False,
            billing_cycle="monthly",
            service_rate_category="consumption",
            sponsor_pi=self.pi1,
            fileset_name=self.fileset1,
            subsidized=False,
        )
        self.alloc2 = AllocationUsageFactory(
            usage_date=self.usage_date,
            exempt=False,
            billing_cycle="monthly",
            service_rate_category="consumption",
            sponsor_pi=self.pi1,
            fileset_name=self.fileset2,
            subsidized=True,
        )
        self.alloc3 = AllocationUsageFactory(
            usage_date=self.usage_date,
            exempt=True,
            billing_cycle="monthly",
            service_rate_category="consumption",
            sponsor_pi=self.pi2,
            fileset_name=self.fileset1,
            subsidized=False,
        )
        self.alloc4 = AllocationUsageFactory(
            usage_date=self.usage_date,
            exempt=False,
            billing_cycle="prepaid",
            service_rate_category="subscription",
            sponsor_pi=self.pi2,
            fileset_name=self.fileset2,
            subsidized=False,
        )
        self.alloc5 = AllocationUsageFactory(
            usage_date=self.usage_date,
            exempt=False,
            billing_cycle="monthly",
            service_rate_category="consumption",
            sponsor_pi=self.pi2,
            fileset_name=self.fileset3,
            subsidized=False,
        )

    def test_monthly_billable(self):
        qs = AllocationUsage.objects.monthly_billable(self.usage_date)
        self.assertIn(self.alloc1, qs)
        self.assertIn(self.alloc2, qs)
        self.assertNotIn(self.alloc3, qs)
        self.assertNotIn(self.alloc4, qs)
        self.assertIn(self.alloc5, qs)

    def test_with_usage_date(self):
        qs = AllocationUsage.objects.with_usage_date(self.usage_date)
        self.assertEqual(qs.count(), 5)

    def test_not_exempt(self):
        qs = AllocationUsage.objects.not_exempt()
        self.assertIn(self.alloc1, qs)
        self.assertIn(self.alloc2, qs)
        self.assertIn(self.alloc4, qs)
        self.assertIn(self.alloc5, qs)
        self.assertNotIn(self.alloc3, qs)

    def test_consumption(self):
        qs = AllocationUsage.objects.consumption()
        self.assertIn(self.alloc1, qs)
        self.assertIn(self.alloc2, qs)
        self.assertIn(self.alloc3, qs)
        self.assertIn(self.alloc5, qs)
        self.assertNotIn(self.alloc4, qs)

    def test_by_fileset(self):
        qs = AllocationUsage.objects.by_fileset(self.fileset1)
        self.assertIn(self.alloc1, qs)
        self.assertIn(self.alloc3, qs)
        self.assertNotIn(self.alloc2, qs)
        self.assertNotIn(self.alloc4, qs)
        self.assertNotIn(self.alloc5, qs)

    def test_by_pi(self):
        qs = AllocationUsage.objects.by_pi(self.pi1)
        self.assertIn(self.alloc1, qs)
        self.assertIn(self.alloc2, qs)
        self.assertNotIn(self.alloc3, qs)
        self.assertNotIn(self.alloc4, qs)
        self.assertNotIn(self.alloc5, qs)

    def test__count_subsidized_by_pi(self):
        qs = AllocationUsage.objects.monthly_billable(self.usage_date).consumption()
        count = qs._count_subsidized_by_pi(self.pi1)
        self.assertEqual(count, 1)
        count2 = qs._count_subsidized_by_pi(self.pi2)
        self.assertEqual(count2, 0)

    def test__is_subsidized_valid_by_pi(self):
        qs = AllocationUsage.objects.monthly_billable(self.usage_date).consumption()
        self.assertTrue(qs._is_subsidized_valid_by_pi(self.pi1))
        self.assertTrue(qs._is_subsidized_valid_by_pi(self.pi2))

    def test__is_all_subsidized_valid(self):
        qs = AllocationUsage.objects.monthly_billable(self.usage_date).consumption()
        self.assertTrue(qs._is_all_subsidized_valid())
        # Add another subsidized for pi1 to make it invalid
        AllocationUsageFactory(
            usage_date=self.usage_date,
            exempt=False,
            billing_cycle="monthly",
            service_rate_category="consumption",
            sponsor_pi=self.pi1,
            fileset_name="filesetD",
            subsidized=True,
        )
        qs2 = AllocationUsage.objects.monthly_billable(self.usage_date).consumption()
        self.assertFalse(qs2._is_all_subsidized_valid())

    def test_set_and_validate_all_subsidized(self):
        qs = AllocationUsage.objects.monthly_billable(self.usage_date).consumption()
        # pi2 has no subsidized, should set one
        self.assertTrue(qs.set_and_validate_all_subsidized())
        # After running, pi2 should have one subsidized
        qs_refresh = AllocationUsage.objects.monthly_billable(self.usage_date).consumption()
        self.assertTrue(qs_refresh._is_all_subsidized_valid())
        self.assertEqual(qs_refresh._count_subsidized_by_pi(self.pi2), 1)

    def test__set_subsidized_by_pi(self):
        qs = AllocationUsage.objects.monthly_billable(self.usage_date).consumption()
        # pi2 has no subsidized, should set one
        result = qs._set_subsidized_by_pi(self.pi2)
        self.assertTrue(result)
        qs_refresh = AllocationUsage.objects.monthly_billable(self.usage_date).consumption()
        self.assertEqual(qs_refresh._count_subsidized_by_pi(self.pi2), 1)
