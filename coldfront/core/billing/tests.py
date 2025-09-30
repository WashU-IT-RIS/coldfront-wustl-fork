from django.test import TestCase
from .factories import AllocationUsageFactory
from .models import AllocationUsage

class AllocationUsageTest(TestCase):
	def test_allocation_usage_factory(self):
		usage = AllocationUsageFactory()
		self.assertIsInstance(usage, AllocationUsage)
		self.assertTrue(isinstance(usage.external_key, int))
		self.assertTrue(isinstance(usage.source, str))
		self.assertTrue(isinstance(usage.sponsor_pi, str))
		self.assertTrue(isinstance(usage.billing_contact, str))
		self.assertTrue(isinstance(usage.fileset_name, str))
		self.assertTrue(isinstance(usage.service_rate_category, str))
		self.assertTrue(isinstance(usage.usage, str))
		self.assertTrue(isinstance(usage.funding_number, str))
		self.assertTrue(isinstance(usage.exempt, bool))
		self.assertTrue(isinstance(usage.subsidized, bool))
		self.assertTrue(isinstance(usage.is_condo_group, bool))
		self.assertTrue(isinstance(usage.parent_id_key, int))
		self.assertTrue(isinstance(usage.quota, str))
		self.assertTrue(isinstance(usage.billing_cycle, str))
		self.assertIsNotNone(usage.usage_timestamp)
		self.assertIsNotNone(usage.ingestion_date)
		self.assertTrue(isinstance(usage.storage_cluster, str))
