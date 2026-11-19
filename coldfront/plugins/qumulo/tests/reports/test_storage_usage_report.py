from django.test import TestCase
from unittest.mock import patch
from datetime import date
from coldfront.core.test_helpers.factories import (
    AllocationFactory,
    AllocationAttributeFactory,
    AllocationAttributeTypeFactory,
    AllocationAttributeUsageFactory,
    AllocationStatusChoiceFactory,
    ProjectFactory,
    ResourceFactory,
    ResourceTypeFactory,
)
from coldfront.core.project.models import Project
from coldfront.plugins.qumulo.tests import fixtures
from coldfront.plugins.qumulo.reports.storage_usage_report import (
    NO_USAGE_DATA,
    StorageUsageReport,
)
import re


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
            {"pi": "alice", "usage_kb": "12345.0", "filesystem_path": "/fs1"},
            {"pi": "bob", "usage_kb": "67890.0", "filesystem_path": "/fs2"},
        ]
        table = self.report._format_usage_report(usages)
        self.assertIn("PI", table)
        self.assertIn("Usage (KB)", table)
        self.assertNotIn("Usage (GB)", table)
        self.assertIn("alice", table)
        self.assertIn("/fs1", table)
        self.assertIn("67,890", table)
        self.assertNotIn("67,890.00", table)

    def test_format_usage_report_table_gb_tb(self):
        usages = [
            {"pi": "alice", "usage_kb": str(5 * 1024**2), "filesystem_path": "/fs1"},
            {"pi": "bob", "usage_kb": str(2.5 * 1024**3), "filesystem_path": "/fs2"},
        ]
        table = self.report._format_usage_report(
            self.report._convert_usage_units(usages)
        )
        header = table.splitlines()[0]
        self.assertIn("PI", header)
        self.assertIn("Usage (GB)", header)
        self.assertIn("Usage (TB)", header)
        self.assertNotIn("Usage (KB)", header)
        self.assertLess(header.index("Usage (GB)"), header.index("Usage (TB)"))
        self.assertIn("alice", table)
        self.assertIn("/fs1", table)
        # alice: 5 GB, 0.00 TB; bob: 2,560 GB, 2.50 TB
        self.assertIn("5.00", table)
        self.assertIn("2,560.00", table)
        self.assertIn("2.50", table)

    @patch("coldfront.plugins.qumulo.reports.storage_usage_report.ItsmClientHandler")
    def test_get_departments_by_school(self, mock_itsm):
        mock_instance = mock_itsm.return_value
        mock_instance.url = "http://test/service_provision"
        mock_instance.get_data.return_value = [{"number": "CH123"}, {"number": "AU456"}]
        result = self.report.get_departments_by_school("ENG")
        self.assertEqual(result, ["CH123", "AU456"])

    def test_format_filter_for_dept_by_unit(self):
        result = self.report._format_filter_for_dept_by_unit("ENG")
        self.assertIn("unit", result)
        result_all = self.report._format_filter_for_dept_by_unit("ALL")
        self.assertNotIn("unit", result_all)

    def test_filter_for_valid_dept_number(self):
        result = self.report._filter_for_valid_dept_number()
        self.assertIn("operator", result)
        self.assertIn("^CH|^AU", result)
        regex = r"^CH|^AU"
        self.assertIsNone(re.match(regex, "abc123"))
        self.assertIsNone(re.match(regex, "ABCH000"))

    def test_get_allocations_by_school_with_factory(self):
        # Create a department attribute type and allocation
        dept_type = AllocationAttributeTypeFactory(name="department_number")
        alloc1 = AllocationFactory()
        alloc1.status.name = "Active"
        alloc1.save()
        AllocationAttributeFactory(
            allocation=alloc1, allocation_attribute_type=dept_type, value="CH123"
        )
        alloc2 = AllocationFactory()
        alloc2.status.name = "Active"
        alloc2.save()
        AllocationAttributeFactory(
            allocation=alloc2, allocation_attribute_type=dept_type, value="AU456"
        )
        # Patch get_departments_by_school to return the test value
        self.report.get_departments_by_school = lambda school: ["CH123", "AU456"]
        allocs = list(self.report.get_allocations_by_school("ENG"))
        expected = sorted([alloc1.id, alloc2.id])
        actual = sorted([a.id for a in allocs])
        self.assertEqual(actual, expected)

    def test_get_allocations_by_project_returns_only_active_allocations_for_project(
        self,
    ):
        project = ProjectFactory()
        other_project = ProjectFactory()
        active_alloc = AllocationFactory(project=project)
        active_alloc.resources.add(self._storage_resource())
        other = AllocationFactory(project=other_project)
        other.resources.add(self._storage_resource())

        allocs = list(self.report.get_allocations_by_project(project.title))
        self.assertEqual(allocs, [active_alloc])

    def test_get_allocations_by_project_excludes_suballocations(self):
        parent = AllocationFactory()
        parent.resources.add(self._storage_resource())
        # AllocationFactory gets-or-creates by project, so move the child after
        child = AllocationFactory()
        child.project = parent.project
        child.save()
        child.resources.add(self._storage_resource())
        fixtures.create_allocation_linkage(parent, [child])

        allocs = self.report.get_allocations_by_project(parent.project.title)
        self.assertEqual(list(allocs), [parent])

    def test_get_allocations_by_project_excludes_non_storage_allocations(self):
        allocation = AllocationFactory()
        allocation.resources.add(
            ResourceFactory(
                name="compute", resource_type=ResourceTypeFactory(name="Cluster")
            )
        )

        allocs = self.report.get_allocations_by_project(allocation.project.title)
        self.assertEqual(allocs.count(), 0)

    def test_get_allocations_by_project_excludes_inactive_allocations(self):
        project = ProjectFactory()
        AllocationFactory(
            project=project, status=AllocationStatusChoiceFactory(name="Inactive")
        )

        allocs = self.report.get_allocations_by_project(project.title)
        self.assertEqual(allocs.count(), 0)

    def test_get_allocations_by_project_unknown_project_raises(self):
        with self.assertRaises(Project.DoesNotExist):
            self.report.get_allocations_by_project("no-such-project")

    def test_get_suballocation_ids_with_factory(self):
        # Create parent and child allocations
        parent_alloc = AllocationFactory()
        parent_alloc.status.name = "Active"
        parent_alloc.save()
        child_alloc1 = AllocationFactory()
        child_alloc1.status.name = "Active"
        child_alloc1.save()
        child_alloc2 = AllocationFactory()
        child_alloc2.status.name = "Active"
        child_alloc2.save()
        # Create linkage
        linkage = fixtures.create_allocation_linkage(
            parent_alloc, [child_alloc1, child_alloc2]
        )
        ids = self.report._get_suballocation_ids()
        expected_ids = {child_alloc1.id, child_alloc2.id}
        self.assertEqual(set(ids), expected_ids)

    def test_get_usages_by_pi_for_school_with_factory(self):
        # Setup allocation and usage
        allocation = AllocationFactory()
        allocation.status.name = "Active"
        allocation.save()
        AllocationAttributeFactory(
            allocation=allocation,
            allocation_attribute_type=AllocationAttributeTypeFactory(
                name="department_number"
            ),
            value="CH123",
        )
        AllocationAttributeFactory(
            allocation=allocation,
            allocation_attribute_type=AllocationAttributeTypeFactory(
                name="storage_filesystem_path"
            ),
            value="/fs1",
        )
        usage = AllocationAttributeUsageFactory(
            allocation_attribute=AllocationAttributeFactory(
                allocation=allocation,
                allocation_attribute_type=AllocationAttributeTypeFactory(
                    name="storage_quota"
                ),
                value=2048,
            ),
            value=2048,
        )
        usage.history.create(
            allocation_attribute=usage.allocation_attribute,
            value=2048,
            history_date=self.usage_date,
        )

        self.report.get_departments_by_school = lambda school: ["CH123"]
        usages = self.report.get_usages_by_pi_for_school("ENG")
        self.assertTrue(any(u["pi"] == allocation.project.pi.username for u in usages))
        self.assertTrue(any(u["filesystem_path"] == "/fs1" for u in usages))

    def _storage_resource(self):
        return ResourceFactory(
            name="Storage2", resource_type=ResourceTypeFactory(name="Storage")
        )

    def _add_usage(self, allocation, path, value=2048):
        allocation.resources.add(self._storage_resource())
        AllocationAttributeFactory(
            allocation=allocation,
            allocation_attribute_type=AllocationAttributeTypeFactory(
                name="storage_filesystem_path"
            ),
            value=path,
        )
        usage = AllocationAttributeUsageFactory(
            allocation_attribute=AllocationAttributeFactory(
                allocation=allocation,
                allocation_attribute_type=AllocationAttributeTypeFactory(
                    name="storage_quota"
                ),
                value=value,
            ),
            value=value,
        )
        usage.history.create(
            allocation_attribute=usage.allocation_attribute,
            value=value,
            history_date=self.usage_date,
        )

    def test_get_usages_for_project_with_factory(self):
        allocation = AllocationFactory()
        self._add_usage(allocation, "/fs1")

        usages = self.report.get_usages_for_project(allocation.project.title)
        self.assertEqual(len(usages), 1)
        self.assertNotIn("pi", usages[0])
        self.assertEqual(usages[0]["filesystem_path"], "/fs1")

    def test_get_usages_for_project_excludes_other_projects(self):
        allocation = AllocationFactory()
        self._add_usage(allocation, "/fs1")
        other = AllocationFactory()
        self._add_usage(other, "/fs2")

        usages = self.report.get_usages_for_project(allocation.project.title)
        paths = [u["filesystem_path"] for u in usages]
        self.assertEqual(paths, ["/fs1"])

    def test_get_usages_for_project_no_usage_shows_no_data_row(self):
        allocation = AllocationFactory()
        allocation.resources.add(self._storage_resource())
        usages = self.report.get_usages_for_project(allocation.project.title)
        self.assertEqual(len(usages), 1)
        self.assertEqual(usages[0]["usage_kb"], NO_USAGE_DATA)

    def test_format_usage_report_with_no_data_rows(self):
        usages = [
            {"usage_kb": str(5 * 1024**2), "filesystem_path": "/fs1"},
            {"usage_kb": NO_USAGE_DATA, "filesystem_path": "/fs2"},
        ]
        table = self.report._format_usage_report(
            self.report._convert_usage_units(usages)
        )
        rows = table.splitlines()[2:]
        self.assertIn("5.00", rows[0])
        self.assertIn("/fs1", rows[0])
        self.assertEqual(rows[1].count(NO_USAGE_DATA), 2)
        self.assertIn("/fs2", rows[1])
        # Numeric columns stay right-aligned and the same width
        self.assertEqual(len(rows[0]), len(rows[1]))

    def test_get_usages_for_project_one_row_per_allocation(self):
        allocation = AllocationFactory()
        self._add_usage(allocation, "/fs2")
        second = AllocationFactory()
        second.project = allocation.project
        second.save()
        self._add_usage(second, "/fs1", value=4096)
        with patch.object(
            self.report,
            "get_allocations_by_project",
            return_value=[allocation, second],
        ):
            usages = self.report.get_usages_for_project(allocation.project.title)
        self.assertEqual(len(usages), 2)
        # Sorted by filesystem path
        self.assertEqual([u["filesystem_path"] for u in usages], ["/fs1", "/fs2"])
        self.assertEqual([float(u["usage_kb"]) for u in usages], [4.0, 2.0])

    def test_generate_report_for_project(self):
        allocation = AllocationFactory()
        self._add_usage(allocation, "/fs1")

        report = self.report.generate_report_for_project(allocation.project.title)
        table_header = report.split("\n\n", 1)[1].splitlines()[0]
        self.assertNotIn("PI", table_header)
        self.assertIn("/fs1", report)
        self.assertIn("Usage (GB)", report)
        self.assertIn("Usage (TB)", report)
        self.assertNotIn("Usage (KB)", report)

    def test_get_project_summary(self):
        allocation = AllocationFactory()
        # storage_quota is in TB; usage value is in bytes
        self._add_usage(allocation, "/fs1", value=10)
        second = AllocationFactory()
        second.project = allocation.project
        second.save()
        self._add_usage(second, "/fs2", value=10)
        used_kb = {allocation.pk: 6 * 1024**3, second.pk: 1.5 * 1024**3}
        with patch.object(
            self.report,
            "get_allocations_by_project",
            return_value=[allocation, second],
        ), patch.object(
            type(allocation),
            "get_usage_kb_by_date",
            autospec=True,
            side_effect=lambda alloc, _date: used_kb[alloc.pk],
        ):
            summary = self.report.get_project_summary(allocation.project.title)

        self.assertEqual(summary["total_quota_tb"], 1000)
        self.assertEqual(summary["allocated_tb"], 20)
        self.assertEqual(summary["unallocated_tb"], 980)
        self.assertAlmostEqual(summary["used_tb"], 7.5)

    def test_format_project_summary(self):
        text = self.report._format_project_summary(
            {
                "total_quota_tb": 100.0,
                "allocated_tb": 27.0,
                "unallocated_tb": 73.0,
                "used_tb": 18.9,
            }
        )
        self.assertEqual(
            text,
            "Total condo quota: 100 TB\n"
            "Allocated to PIs: 27 TB (27.000%)\n"
            "Unallocated: 73 TB\n"
            "Used: 18.900 TB (70.000% of allocated)",
        )

    def test_format_project_summary_nothing_allocated(self):
        text = self.report._format_project_summary(
            {
                "total_quota_tb": 100.0,
                "allocated_tb": 0.0,
                "unallocated_tb": 100.0,
                "used_tb": 0.0,
            }
        )
        self.assertIn("Allocated to PIs: 0 TB (0.000%)", text)
        self.assertIn("Used: 0.000 TB (N/A of allocated)", text)

    def test_generate_report_for_project_starts_with_summary(self):
        allocation = AllocationFactory()
        self._add_usage(allocation, "/fs1")

        report = self.report.generate_report_for_project(allocation.project.title)
        self.assertTrue(report.startswith("Total condo quota: "))
        self.assertLess(report.index("Used: "), report.index("Usage (GB)"))

    def test_generate_report_for_school(self):
        # Setup allocation and usage
        allocation = AllocationFactory()
        allocation.status.name = "Active"
        allocation.save()
        AllocationAttributeFactory(
            allocation=allocation,
            allocation_attribute_type=AllocationAttributeTypeFactory(
                name="department_number"
            ),
            value="CH123",
        )
        AllocationAttributeFactory(
            allocation=allocation,
            allocation_attribute_type=AllocationAttributeTypeFactory(
                name="storage_filesystem_path"
            ),
            value="/fs1",
        )
        usage = AllocationAttributeUsageFactory(
            allocation_attribute=AllocationAttributeFactory(
                allocation=allocation,
                allocation_attribute_type=AllocationAttributeTypeFactory(
                    name="storage_quota"
                ),
                value=2048,
            ),
            value=2048,
        )
        usage.history.create(
            allocation_attribute=usage.allocation_attribute,
            value=2048,
            history_date=self.usage_date,
        )

        self.report.get_departments_by_school = lambda school: ["CH123"]
        report = self.report.generate_report_for_school("ENG")
        self.assertIn("PI", report)
        self.assertIn("/fs1", report)
        self.assertIn("Usage (KB)", report)
        self.assertNotIn("Usage (GB)", report)
        self.assertNotIn("Usage (TB)", report)

    def test_allocation_with_no_usage_is_excluded(self):
        """
        Allocations with no recorded usage for the date should be excluded from the report.
        """
        # Setup allocation with no usage
        dept_type = AllocationAttributeTypeFactory(name="department_number")
        alloc = AllocationFactory()
        alloc.status.name = "Active"
        alloc.save()
        AllocationAttributeFactory(
            allocation=alloc, allocation_attribute_type=dept_type, value="CH999"
        )
        # Patch get_departments_by_school to return the test value
        self.report.get_departments_by_school = lambda school: ["CH999"]
        # get_allocations_by_school should include the allocation
        allocs = list(self.report.get_allocations_by_school("ENG"))
        self.assertIn(alloc, allocs)

        # But get_usages_by_pi_for_school should exclude it since there is no usage
        usages = self.report.get_usages_by_pi_for_school("ENG")
        # Should be empty since no usage is recorded
        self.assertEqual(usages, [])
