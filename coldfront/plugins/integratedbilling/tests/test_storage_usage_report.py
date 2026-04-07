import unittest
from unittest.mock import patch, MagicMock
from datetime import date
from coldfront.plugins.integratedbilling.storage_usage_report import (
    ItsmServiceUsage,
    ColdfrontServiceUsage,
    ItsmDepartmentClient,
    StorageUsageReport,
    QUERY_ATTRIBUTE,
)


class TestItsmServiceUsage(unittest.TestCase):
    @patch("coldfront.plugins.integratedbilling.storage_usage_report.ItsmClientHandler")
    def test_get_data(self, MockItsmClientHandler):
        mock_handler = MockItsmClientHandler.return_value
        mock_handler.get_data.return_value = [
            {
                QUERY_ATTRIBUTE["usage_date"]["itsm"]: "2024-01-01T00:00:00Z",
                QUERY_ATTRIBUTE["service"]["itsm"]: "service1",
                QUERY_ATTRIBUTE["dept_number"]["itsm"]: "123",
                QUERY_ATTRIBUTE["pi"]["itsm"]: "piuser",
                QUERY_ATTRIBUTE["service_rate_category"]["itsm"]: "cat1",
                QUERY_ATTRIBUTE["usage"]["itsm"]: "100KB",
            }
        ]
        usage = ItsmServiceUsage(date(2024, 1, 1))
        data = usage.get_data()
        self.assertEqual(len(data), 1)
        mock_handler.get_data.assert_called()

    def test_normalized_to_coldfront_report(self):
        usage = ItsmServiceUsage(date(2024, 1, 1))
        raw_report = [
            {
                QUERY_ATTRIBUTE["usage_date"]["itsm"]: "2024-01-01T00:00:00Z",
                QUERY_ATTRIBUTE["service"]["itsm"]: "service1",
                QUERY_ATTRIBUTE["dept_number"]["itsm"]: "123",
                QUERY_ATTRIBUTE["pi"]["itsm"]: "piuser",
                QUERY_ATTRIBUTE["service_rate_category"]["itsm"]: "cat1",
                QUERY_ATTRIBUTE["usage"]["itsm"]: "100KB",
            }
        ]
        normalized = usage.normalized_to_coldfront_report(raw_report)
        self.assertEqual(
            normalized[0][QUERY_ATTRIBUTE["usage_date"]["coldfront"]], "2024-01-01"
        )
        self.assertEqual(normalized[0][QUERY_ATTRIBUTE["usage"]["coldfront"]], 100)


class TestColdfrontServiceUsage(unittest.TestCase):
    @patch(
        "coldfront.plugins.integratedbilling.storage_usage_report.ColdFrontStorageUsageReport"
    )
    def test_get_data(self, MockColdFrontStorageUsageReport):
        mock_report = MockColdFrontStorageUsageReport.return_value
        mock_allocation = MagicMock()
        mock_allocation.get_attribute.side_effect = lambda k: (
            "val" if k != QUERY_ATTRIBUTE["dept_number"]["coldfront"] else "dept123"
        )
        mock_allocation.project.pi.username = "piuser"
        mock_allocation.get_usage_kb_by_date.return_value = "200"
        mock_report.get_allocations.return_value = [mock_allocation]
        usage = ColdfrontServiceUsage(date(2024, 1, 1))
        data = usage.get_data()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0][QUERY_ATTRIBUTE["usage"]["coldfront"]], 200)
        self.assertEqual(data[0][QUERY_ATTRIBUTE["pi"]["coldfront"]], "piuser")


class TestItsmDepartmentClient(unittest.TestCase):
    def setUp(self):
        self.client = ItsmDepartmentClient()

    @patch("coldfront.plugins.integratedbilling.storage_usage_report.ItsmClientHandler")
    def test_init_sets_attributes(self, mock_handler):
        client = ItsmDepartmentClient()
        self.assertEqual(client.attributes, ["number", "unit", "name"])
        self.assertIsNotNone(client.itsm_client)

    def test_format_filter_for_dept(self):
        expected = '{"number":{"operator":"~*","value":["^CH|^AU"]}}'
        self.assertEqual(
            self.client._ItsmDepartmentClient__format_filter_for_dept(), expected
        )

    @patch.object(
        ItsmDepartmentClient,
        "_ItsmDepartmentClient__format_filter_for_dept",
        return_value="{}",
    )
    @patch("coldfront.plugins.integratedbilling.storage_usage_report.ItsmClientHandler")
    def test_get_dictionary_by_number(self, mock_handler, mock_filter):
        mock_instance = mock_handler.return_value
        mock_instance.get_data.return_value = [
            {"number": "CH123", "unit": "Unit1", "name": "Dept1"},
            {"number": "AU456", "unit": "Unit2", "name": "Dept2"},
        ]
        client = ItsmDepartmentClient()
        result = client.get_dictionary_by_number()
        expected = {
            "CH123": {"number": "CH123", "unit": "Unit1", "name": "Dept1"},
            "AU456": {"number": "AU456", "unit": "Unit2", "name": "Dept2"},
        }
        self.assertEqual(result, expected)


class TestStorageUsageReport(unittest.TestCase):
    def test_init(self):
        usage = StorageUsageReport(date(2024, 1, 1))
        self.assertEqual(usage.usage_date, date(2024, 1, 1))


# Additional tests for private methods of StorageUsageReport
class TestStorageUsageReportPrivateMethods(unittest.TestCase):
    def setUp(self):
        self.usage_date = date(2024, 1, 1)
        self.report = StorageUsageReport(self.usage_date)
        # Patch tier to avoid attribute errors in __format_csv_usage_report
        self.report.tier = MagicMock()
        self.report.tier.name = "Active"

    def test_sort_usage_data(self):
        data = [
            {"usage_date": "2024-01-02", "pi": "b"},
            {"usage_date": "2024-01-01", "pi": "a"},
        ]
        sorted_data = self.report._StorageUsageReport__sort_usage_data(
            data, ["usage_date", "pi"]
        )
        self.assertEqual(sorted_data[0]["usage_date"], "2024-01-01")
        self.assertEqual(sorted_data[1]["usage_date"], "2024-01-02")

    def test_group_usage_data(self):
        # Use coldfront_attribute for correct keys
        usage_key = self.report.report_attribute["usage"]
        pi_key = self.report.report_attribute["pi"]
        data = [
            {pi_key: "a", usage_key: 100},
            {pi_key: "a", usage_key: 200},
            {pi_key: "b", usage_key: 50},
        ]
        grouped = self.report._StorageUsageReport__group_usage_data(data, [pi_key])
        # Should sum usages for same pi
        a_entry = next(e for e in grouped if e[pi_key] == "a")
        b_entry = next(e for e in grouped if e[pi_key] == "b")
        self.assertEqual(a_entry[usage_key], 300)
        self.assertEqual(b_entry[usage_key], 50)

    def test_append_dept_unit_name_to_usage_data(self):
        coldfront = self.report.report_attribute
        usage_data = [
            {
                coldfront["dept_number"]: "D1",
                coldfront["usage_date"]: "2024-01-01",
                coldfront["service"]: 1,
                coldfront["pi"]: "piuser",
            },
            {
                coldfront["dept_number"]: "D2",
                coldfront["usage_date"]: "2024-01-01",
                coldfront["service"]: 1,
                coldfront["pi"]: "piuser2",
            },
        ]
        dept_dictionary = {
            "D1": {"unit": "School1", "name": "Dept1"},
            "D2": {"unit": "School2", "name": "Dept2"},
        }
        result = self.report._StorageUsageReport__append_dept_unit_name_to_usage_data(
            usage_data, dept_dictionary
        )
        # Check that unit and name are set correctly
        self.assertEqual(result[0]["unit"], "School1")
        self.assertEqual(result[0]["name"], "Dept1")
        self.assertEqual(result[1]["unit"], "School2")
        self.assertEqual(result[1]["name"], "Dept2")

    def test_format_csv_usage_report(self):
        coldfront = self.report.report_attribute
        data = [
            {
                "fiscal_year": "FY24",
                "usage_month": "2024-01",
                "service": "Storage Active",
                "unit": "School1",
                "name": "Dept1",
                coldfront["pi"]: "piuser",
                coldfront["service_rate_category"]: "Tier1",
                coldfront["usage"]: 1234,
            }
        ]
        result = self.report._StorageUsageReport__format_csv_usage_report(data)
        self.assertIn("Fiscal Year", result)
        self.assertIn("School1", result)
        self.assertIn("1234", result)


if __name__ == "__main__":
    unittest.main()
