from django.test import TestCase
from unittest.mock import patch
from datetime import date
from coldfront.core.test_helpers.factories import (
    AllocationFactory, AllocationAttributeFactory, AllocationAttributeTypeFactory, AllocationAttributeUsageFactory, ResourceFactory
)
from coldfront.plugins.qumulo.tests import fixtures
from coldfront.plugins.qumulo.reports.storage_usage_report import StorageUsageReport

class StorageUsageReportFactoryTests(TestCase):
    def setUp(self):
        fixtures.create_metadata_for_testing()
        self.usage_date = date(2024, 1, 1)
        self.report = StorageUsageReport(usage_date=self.usage_date)

    def test_format_usage_report_empty(self):
        result = self.report._format_usage_report([])
        self.assertEqual(result, "No usage data available.")

    def test_format_usage_report_table(self):
        usages = [
            {'pi': 'alice', 'usage_kb': '12345.0', 'filesystem_path': '/fs1'},
            {'pi': 'bob', 'usage_kb': '67890.0', 'filesystem_path': '/fs2'}
        ]
        table = self.report._format_usage_report(usages)
        self.assertIn('PI', table)
        self.assertIn('alice', table)
        self.assertIn('/fs1', table)
        self.assertIn('67,890', table)

    @patch('coldfront.plugins.qumulo.reports.storage_usage_report.ItsmClientHandler')
    def test_get_departments_by_school(self, mock_itsm):
        mock_instance = mock_itsm.return_value
        mock_instance.url = 'http://test/service_provision'
        mock_instance.get_data.return_value = [{'number': 'CH123'}, {'number': 'AU456'}]
        result = self.report.get_departments_by_school('ENG')
        self.assertEqual(result, ['CH123', 'AU456'])

    def test_format_filter_for_dept_by_unit(self):
        result = self.report._format_filter_for_dept_by_unit('ENG')
        self.assertIn('unit', result)
        result_all = self.report._format_filter_for_dept_by_unit('ALL')
        self.assertNotIn('unit', result_all)

    def test_filter_for_valid_dept_number(self):
        result = self.report._filter_for_valid_dept_number()
        self.assertIn('operator', result)
        self.assertIn('^CH|^AU', result)

    def test_get_allocations_by_school_with_factory(self):
        # Create a department attribute type and allocation
        dept_type = AllocationAttributeTypeFactory(name='department_number')
        alloc1 = AllocationFactory()
        alloc1.status.name = 'Active'
        alloc1.save()
        AllocationAttributeFactory(
            allocation=alloc1,
            allocation_attribute_type=dept_type,
            value='CH123'
        )
        alloc2 = AllocationFactory()
        alloc2.status.name = 'Active'
        alloc2.save()
        AllocationAttributeFactory(
            allocation=alloc2,
            allocation_attribute_type=dept_type,
            value='AU456'
        )
        # Patch get_departments_by_school to return the test value
        self.report.get_departments_by_school = lambda school: ['CH123', 'AU456']
        allocs = list(self.report.get_allocations_by_school('ENG'))
        expected = sorted([alloc1.id, alloc2.id])
        actual = sorted([a.id for a in allocs])
        self.assertEqual(actual, expected)

    def test_get_suballocation_ids_with_factory(self):
        # Create parent and child allocations
        parent_alloc = AllocationFactory()
        parent_alloc.status.name = 'Active'
        parent_alloc.save()
        child_alloc1 = AllocationFactory()
        child_alloc1.status.name = 'Active'
        child_alloc1.save()
        child_alloc2 = AllocationFactory()
        child_alloc2.status.name = 'Active'
        child_alloc2.save()
        # Create linkage
        linkage = fixtures.create_allocation_linkage(parent_alloc, [child_alloc1, child_alloc2])
        ids = self.report._get_suballocation_ids()
        expected_ids = {child_alloc1.id, child_alloc2.id}
        self.assertEqual(set(ids), expected_ids)

    def test_get_usages_by_pi_for_school_with_factory(self):
        # Setup allocation and usage
        allocation = AllocationFactory()
        allocation.status.name = 'Active'
        allocation.save()
        AllocationAttributeFactory(
            allocation=allocation,
            allocation_attribute_type=AllocationAttributeTypeFactory(name='department_number'),
            value='CH123'
        )
        AllocationAttributeFactory(
            allocation=allocation,
            allocation_attribute_type=AllocationAttributeTypeFactory(name='storage_filesystem_path'),
            value='/fs1'
        )
        AllocationAttributeUsageFactory(
            allocation_attribute=AllocationAttributeFactory(
                allocation=allocation,
                allocation_attribute_type=AllocationAttributeTypeFactory(name='storage_quota'),
                value=2048
            ),
            value=2048
        )
        self.report.get_departments_by_school = lambda school: ['CH123']
        usages = self.report.get_usages_by_pi_for_school('ENG')
        self.assertTrue(any(u['pi'] == allocation.project.pi.username for u in usages))
        self.assertTrue(any(u['filesystem_path'] == '/fs1' for u in usages))

    def test_generate_report_for_school(self):
        # Setup allocation and usage
        allocation = AllocationFactory()
        allocation.status.name = 'Active'
        allocation.save()
        AllocationAttributeFactory(
            allocation=allocation,
            allocation_attribute_type=AllocationAttributeTypeFactory(name='department_number'),
            value='CH123'
        )
        AllocationAttributeFactory(
            allocation=allocation,
            allocation_attribute_type=AllocationAttributeTypeFactory(name='storage_filesystem_path'),
            value='/fs1'
        )
        AllocationAttributeUsageFactory(
            allocation_attribute=AllocationAttributeFactory(
                allocation=allocation,
                allocation_attribute_type=AllocationAttributeTypeFactory(name='storage_quota'),
                value=2048
            ),
            value=2048
        )
        self.report.get_departments_by_school = lambda school: ['CH123']
        report = self.report.generate_report_for_school('ENG')
        self.assertIn('PI', report)
        self.assertIn('/fs1', report)
