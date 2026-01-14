import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, date, time
from coldfront.plugins.qumulo.utils.storage_usage_report import StorageUsageReport

class TestStorageUsageReport(unittest.TestCase):
    def setUp(self):
        self.report = StorageUsageReport(usage_date=datetime(2024, 1, 1))

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

    def test_is_float(self):
        self.assertTrue(StorageUsageReport._is_float('123.45'))
        self.assertTrue(StorageUsageReport._is_float(123.45))
        self.assertFalse(StorageUsageReport._is_float('abc'))
        self.assertFalse(StorageUsageReport._is_float(None))

    @patch('coldfront.plugins.qumulo.utils.storage_usage_report.ItsmClientHandler')
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
        self.assertIn('CH|AU', result)

    @patch('coldfront.plugins.qumulo.utils.storage_usage_report.Allocation')
    def test_get_allocations_by_school(self, mock_allocation):
        mock_allocation.objects.filter.return_value.exclude.return_value.distinct.return_value = ['alloc1', 'alloc2']
        self.report.get_departments_by_school = MagicMock(return_value=['CH123', 'AU456'])
        result = self.report.get_allocations_by_school('ENG')
        self.assertEqual(result, ['alloc1', 'alloc2'])

    @patch('coldfront.plugins.qumulo.utils.storage_usage_report.AllocationLinkage')
    def test_get_suballocation_ids(self, mock_allocation_linkage):
        # Setup mock for AllocationLinkage.objects.all()
        mock_child1 = MagicMock()
        mock_child1.pk = 101
        mock_child2 = MagicMock()
        mock_child2.pk = 202
        mock_children = MagicMock()
        mock_children.all.return_value = [mock_child1, mock_child2]
        mock_linkage = MagicMock()
        mock_linkage.children = mock_children
        mock_allocation_linkage.objects.all.return_value = [mock_linkage]

        ids = self.report._get_suballocation_ids()
        self.assertEqual(ids, [101, 202])

    @patch('coldfront.plugins.qumulo.utils.storage_usage_report.AllocationAttributeUsage')
    def test_get_allocation_usage_kb_by_date(self, mock_usage):
        mock_usage.history.filter.return_value.values.return_value.first.return_value = {'value': 2048}
        mock_allocation = MagicMock()
        mock_allocation.id = 1
        result = self.report.get_allocation_usage_kb_by_date(mock_allocation, date(2024, 1, 1))
        self.assertEqual(result, 2.0)

    @patch('coldfront.plugins.qumulo.utils.storage_usage_report.StorageUsageReport.get_allocations_by_school')
    @patch('coldfront.plugins.qumulo.utils.storage_usage_report.StorageUsageReport.get_allocation_usage_kb_by_date')
    def test_get_usages_by_pi_for_school(self, mock_usage_kb, mock_allocs):
        mock_alloc = MagicMock()
        mock_alloc.project.pi.username = 'alice'
        mock_alloc.get_attribute.return_value = '/fs1'
        mock_allocs.return_value = [mock_alloc]
        mock_usage_kb.return_value = 100.0
        usages = self.report.get_usages_by_pi_for_school('ENG')
        self.assertEqual(len(usages), 1)
        self.assertEqual(usages[0]['pi'], 'alice')
        self.assertEqual(usages[0]['usage_kb'], '100.0')
        self.assertEqual(usages[0]['filesystem_path'], '/fs1')

    @patch('coldfront.plugins.qumulo.utils.storage_usage_report.StorageUsageReport.get_usages_by_pi_for_school')
    def test_generate_storage_usage_report_for_school(self, mock_usages):
        mock_usages.return_value = [
            {'pi': 'alice', 'usage_kb': '12345.0', 'filesystem_path': '/fs1'}
        ]
        report = self.report.generate_storage_usage_report_for_school('ENG')
        self.assertIn('alice', report)
        self.assertIn('/fs1', report)

if __name__ == "__main__":
    unittest.main()
