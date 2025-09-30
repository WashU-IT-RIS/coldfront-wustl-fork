
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
        self.assertTrue(isinstance(usage.usage, str))
        self.assertTrue(isinstance(usage.funding_number, str))
        self.assertTrue(isinstance(usage.exempt, bool))
        self.assertTrue(isinstance(usage.subsidized, bool))
        self.assertTrue(isinstance(usage.is_condo_group, bool))
        self.assertTrue(isinstance(usage.parent_id_key, int))
        self.assertTrue(isinstance(usage.quota, str))
        self.assertTrue(isinstance(usage.billing_cycle, str))
        self.assertTrue(hasattr(usage, 'usage_timestamp'))
        self.assertTrue(hasattr(usage, 'ingestion_date'))
        self.assertTrue(isinstance(usage.storage_cluster, str))

    def test_allocation_usage_str_fields_not_empty(self):
        usage = AllocationUsageFactory()
        self.assertNotEqual(usage.source, "")
        self.assertNotEqual(usage.sponsor_pi, "")
        self.assertNotEqual(usage.billing_contact, "")
        self.assertNotEqual(usage.fileset_name, "")
        self.assertNotEqual(usage.service_rate_category, "")
        self.assertNotEqual(usage.usage, "")
        self.assertNotEqual(usage.funding_number, "")
        self.assertNotEqual(usage.quota, "")
        self.assertNotEqual(usage.billing_cycle, "")
        self.assertNotEqual(usage.storage_cluster, "")
