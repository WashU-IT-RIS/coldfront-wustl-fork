import pytest
from unittest.mock import MagicMock, patch
from datetime import date
from coldfront.plugins.integratedbilling.storage_usage_report import (
    ItsmServiceUsage,
    ColdfrontServiceUsage,
    ItsmDepartmentClient,
    StorageUsageReport,
)
from coldfront.plugins.integratedbilling.constants import ServiceTiers


@pytest.fixture
def mock_itsm_client():
    with patch(
        "coldfront.plugins.integratedbilling.storage_usage_report.ItsmClientHandler"
    ) as mock:
        yield mock


@pytest.fixture
def mock_coldfront_storage_usage_report():
    with patch(
        "coldfront.plugins.integratedbilling.storage_usage_report.ColdFrontStorageUsageReport"
    ) as mock:
        yield mock


class TestItsmServiceUsage:
    def test_get_data_calls_itsm_client(self, mock_itsm_client):
        mock_instance = mock_itsm_client.return_value
        mock_instance.get_data.return_value = [{"foo": "bar"}]
        usage = ItsmServiceUsage(date(2026, 4, 1))
        result = usage.get_data()
        mock_instance.get_data.assert_called_once()
        assert result == [{"foo": "bar"}]

    def test_normalized_to_coldfront_report(self):
        usage = ItsmServiceUsage(date(2026, 4, 1))
        raw_report = [
            {
                usage.itsm_attribute["usage_date"]: "2026-04-01T00:00:00Z",
                usage.itsm_attribute["usage"]: "123KB",
            }
        ]
        result = usage.normalized_to_coldfront_report(raw_report)
        assert isinstance(result, list)
        assert "usage_date" in result[0]
        assert isinstance(result[0]["usage"], int)


class TestColdfrontServiceUsage:
    def test_get_data(self, mock_coldfront_storage_usage_report):
        mock_instance = mock_coldfront_storage_usage_report.return_value
        mock_allocation = MagicMock()
        mock_allocation.get_attribute.return_value = "dept1"
        mock_allocation.project.pi.username = "pi1"
        mock_allocation.get_usage_kb_by_date.return_value = 100
        mock_instance.get_allocations_by_school.return_value = [mock_allocation]
        usage = ColdfrontServiceUsage(date(2026, 4, 1))
        result = usage.get_data()
        assert isinstance(result, list)
        assert result[0]["usage"] == 100


class TestItsmDepartmentClient:
    def test_get_dictionary_by_number(self, mock_itsm_client):
        mock_instance = mock_itsm_client.return_value
        mock_instance.get_data.return_value = [
            {"number": "CH123", "unit": "Unit1", "name": "Dept1"},
            {"number": "AU456", "unit": "Unit2", "name": "Dept2"},
        ]
        client = ItsmDepartmentClient()
        result = client.get_dictionary_by_number()
        assert "CH123" in result
        assert result["CH123"]["unit"] == "Unit1"


class TestStorageUsageReport:
    @patch("coldfront.plugins.integratedbilling.storage_usage_report.ItsmServiceUsage")
    @patch(
        "coldfront.plugins.integratedbilling.storage_usage_report.ColdfrontServiceUsage"
    )
    @patch(
        "coldfront.plugins.integratedbilling.storage_usage_report.ItsmDepartmentClient"
    )
    def test_generate_report(
        self, mock_dept_client, mock_coldfront_usage, mock_itsm_usage
    ):
        mock_itsm_usage.return_value.get_data.return_value = [
            {
                "usage_date": "2026-04-01",
                "service": 1,
                "dept_number": "CH123",
                "pi": "pi1",
                "service_rate_category": "cat1",
                "usage": 50,
            }
        ]
        mock_itsm_usage.return_value.normalized_to_coldfront_report.return_value = [
            {
                "usage_date": "2026-04-01",
                "service": 1,
                "dept_number": "CH123",
                "pi": "pi1",
                "service_rate_category": "cat1",
                "usage": 50,
            }
        ]
        mock_coldfront_usage.return_value.get_data.return_value = [
            {
                "usage_date": "2026-04-01",
                "service": 1,
                "dept_number": "CH123",
                "pi": "pi1",
                "service_rate_category": "cat1",
                "usage": 100,
            }
        ]
        mock_dept_client.return_value.get_dictionary_by_number.return_value = {
            "CH123": {"unit": "Unit1", "name": "Dept1"}
        }
        report = StorageUsageReport(date(2026, 4, 1), ServiceTiers.Active)
        result = report.generate_report()
        assert "FY26" in result
        assert "Dept1" in result
        assert "150" in result  # 50 + 100
