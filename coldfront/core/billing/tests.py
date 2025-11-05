import os
import tempfile
from datetime import datetime, date
from unittest import mock
from django.test import TestCase
from .factories import AllocationUsageFactory
from coldfront.core.billing.models import AllocationUsage, MonthlyStorageBilling

class AllocationUsageModelTest(TestCase):
    def test_allocation_usage_factory_creates_valid_instance(self):
        usage = AllocationUsageFactory()
        self.assertIsInstance(usage, AllocationUsage)
        self.assertTrue(isinstance(usage.external_key, int))
        self.assertTrue(isinstance(usage.source, str))
        self.assertTrue(isinstance(usage.tier, str))
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
        self.assertNotEqual(usage.tier, "")
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
        self.usage_date = date(2024, 6, 1)
        self.tier_active = "Active"
        self.storage_cluster1 = "Storage1"
        self.storage_cluster2 = "Storage2"
        self.storage_cluster3 = "Storage3"
        self.pi1 = "pi1"
        self.pi2 = "pi2"
        self.fileset1 = "filesetA"
        self.fileset2 = "filesetB"
        self.fileset3 = "filesetC"
        self.fileset4 = "filesetD"
        # Create various AllocationUsage instances
        self.alloc1 = AllocationUsageFactory(
            tier=self.tier_active,
            usage_date=self.usage_date,
            exempt=False,
            billing_cycle="monthly",
            service_rate_category="consumption",
            sponsor_pi=self.pi1,
            storage_cluster=self.storage_cluster1,
            fileset_name=self.fileset1,
            subsidized=False,
        )
        self.alloc2 = AllocationUsageFactory(
            tier=self.tier_active,
            usage_date=self.usage_date,
            exempt=False,
            billing_cycle="monthly",
            service_rate_category="consumption",
            sponsor_pi=self.pi1,
            storage_cluster=self.storage_cluster2,
            fileset_name=self.fileset2,
            subsidized=True,
        )
        self.alloc3 = AllocationUsageFactory(
            tier=self.tier_active,
            usage_date=self.usage_date,
            exempt=True,
            billing_cycle="monthly",
            service_rate_category="consumption",
            sponsor_pi=self.pi2,
            storage_cluster=self.storage_cluster3,
            fileset_name=self.fileset1,
            subsidized=False,
        )
        self.alloc4 = AllocationUsageFactory(
            tier=self.tier_active,
            usage_date=self.usage_date,
            exempt=False,
            billing_cycle="prepaid",
            service_rate_category="subscription",
            sponsor_pi=self.pi2,
            storage_cluster=self.storage_cluster3,
            fileset_name=self.fileset2,
            subsidized=False,
        )
        self.alloc5 = AllocationUsageFactory(
            tier=self.tier_active,
            usage_date=self.usage_date,
            exempt=False,
            billing_cycle="monthly",
            service_rate_category="consumption",
            sponsor_pi=self.pi2,
            storage_cluster=self.storage_cluster3,
            fileset_name=self.fileset3,
            subsidized=False,
        )

        self.alloc6 = AllocationUsageFactory(
            tier=self.tier_active,
            usage_date=self.usage_date,
            exempt=False,
            billing_cycle="monthly",
            service_rate_category="condo",
            sponsor_pi=self.pi2,
            storage_cluster=self.storage_cluster3,
            fileset_name=self.fileset4,
            subsidized=False
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
        self.assertEqual(qs.count(), 6)

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

    def test_manually_exempt_fileset(self):
        qs = AllocationUsage.objects.manually_exempt_fileset(self.fileset1)
        self.assertNotIn(self.alloc1, qs)
        self.assertIn(self.alloc2, qs)
        self.assertNotIn(self.alloc3, qs)
        self.assertIn(self.alloc4, qs)
        self.assertIn(self.alloc5, qs)

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
            tier=self.tier_active,
            usage_date=self.usage_date,
            exempt=False,
            billing_cycle="monthly",
            service_rate_category="consumption",
            sponsor_pi=self.pi1,
            storage_cluster=self.storage_cluster1,
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


class MonthlyStorageBillingTests(TestCase):
    def setUp(self):
        a_delivery_date = date(2024, 5, 1).strftime("%Y-%m-%d")
        a_usage_date = date(2024, 6, 1)
        # Create a fake MonthlyStorageBilling object using AllocationUsageFactory
        self.billing_obj1 = AllocationUsageFactory.build(
            tier="Active",
            usage_date=a_usage_date
        )
        # Add extra attributes for MonthlyStorageBilling
        self.billing_obj1.delivery_date = a_delivery_date
        self.billing_obj1.billable_usage_tb = self.billing_obj1.usage_tb
        self.billing_obj1.billing_unit = "TB"
        self.billing_obj1.unit_rate = "10.00"
        self.billing_obj1.billing_amount = "100.00"

        # Create a fake MonthlyStorageBilling object using AllocationUsageFactory
        self.billing_obj2 = AllocationUsageFactory.build(
            tier="Active",
            usage_date=a_usage_date
        )

        # Add extra attributes for MonthlyStorageBilling
        self.billing_obj2.delivery_date = a_delivery_date
        self.billing_obj2.billable_usage_tb = self.billing_obj2.usage_tb
        self.billing_obj2.billing_unit = "TB"
        self.billing_obj2.unit_rate = "10.00"
        self.billing_obj2.billing_amount = "314.159265"

    def test__copy_template_headers_to_file(self):
        # Create a temp template file with 5 header lines
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as template, \
             tempfile.NamedTemporaryFile(mode="r+", delete=False) as target:
            headers = [f"header{i}\n" for i in range(1, 6)]
            template.writelines(headers)
            template.flush()
            MonthlyStorageBilling._copy_template_headers_to_file(template.name, target.name)
            target.seek(0)
            content = target.readlines()
            self.assertEqual([h.strip() for h in content], [h.strip() for h in headers])
        os.remove(template.name)
        os.remove(target.name)

    def test__read_billing_entry_template(self):
        # Create a temp template file with 6 lines, 6th is billing entry
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as template:
            lines = [f"header{i}\n" for i in range(1, 6)]
            billing_entry = "entry_line"
            lines.append(billing_entry + "\n")
            template.writelines(lines)
            template.flush()
            result = MonthlyStorageBilling._read_billing_entry_template(template.name)
            self.assertEqual(result, billing_entry)
        os.remove(template.name)

    def test__get_fiscal_year_by_delivery_date(self):
        # Patch datetime to June and July to test fiscal year logic
        with mock.patch("coldfront.core.billing.models.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 6, 1)
            fy = MonthlyStorageBilling._get_fiscal_year_by_delivery_date(datetime(2024, 5, 1).date())
            self.assertEqual(fy, "FY24")
            mock_dt.now.return_value = datetime(2024, 7, 1)
            fy = MonthlyStorageBilling._get_fiscal_year_by_delivery_date(datetime(2024, 5, 1).date())
            self.assertEqual(fy, "FY24")
            fy = MonthlyStorageBilling._get_fiscal_year_by_delivery_date(datetime(2024, 6, 1).date())
            self.assertEqual(fy, "FY25")
            fy = MonthlyStorageBilling._get_fiscal_year_by_delivery_date(datetime(2024, 12, 1).date())
            self.assertEqual(fy, "FY25")

    def test_generate_report(self):
        # Prepare template file with 6 lines, 6th is billing entry with placeholders
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as template, \
             tempfile.NamedTemporaryFile(mode="r+", delete=False) as output:
            headers = [f"header{i}\n" for i in range(1, 6)]
            entry_template = (
                "{spreadsheet_key},{document_date},{fiscal_year},{billing_month},"
                "{sponsor_pi},{storage_cluster},{tier},{service_rate_category},"
                "{billable_usage_tb},{unit_rate},{billing_unit},{billing_amount},"
                "{delivery_date},{fileset_name},{funding_number}"
            )
            template.writelines(headers)
            template.write(entry_template + "\n")
            template.flush()

            billing_objects = [self.billing_obj1, self.billing_obj2]
            MonthlyStorageBilling.generate_report(
                billing_objects, template.name, output.name
            )
            output.seek(0)
            lines = output.readlines()
            # Check headers
            self.assertEqual([l.strip() for l in lines[:5]], [h.strip() for h in headers])
            # Check billing entry line
            entry_line = lines[5].strip()
            self.assertIn(self.billing_obj1.sponsor_pi, entry_line)
            self.assertIn(self.billing_obj1.storage_cluster, entry_line)
            self.assertIn("Active", entry_line)
            self.assertIn("TB", entry_line)
            entry_line = lines[6].strip()
            self.assertIn(",314.16,", entry_line)
        os.remove(template.name)
        os.remove(output.name)
