import os
from dotenv import load_dotenv

from coldfront.plugins.qumulo.tests.fixtures import (
    create_metadata_for_testing,
)
from coldfront.plugins.qumulo.tests.utils.mock_data import (
    get_mock_quota_data,
    get_mock_quota_response,
)

load_dotenv(override=True)

from django.test import TestCase

from unittest.mock import patch, MagicMock

from coldfront.plugins.qumulo.services.file_quota_service import FileQuotaService


class TestFileQuotaService(TestCase):

    def setUp(self):
        create_metadata_for_testing()
        self.mock_quota_response = get_mock_quota_response(
            get_mock_quota_data("/storage2-dev/fs1"), "/storage2-dev/fs1"
        )
        return super().setUp()

    @patch.dict(os.environ, {"QUMULO_RESULT_SET_PAGE_LIMIT": "2000"})
    @patch.dict(os.environ, {"ALLOCATION_LIMIT_THRESHOLD": "0.9"})
    @patch("coldfront.plugins.qumulo.services.file_quota_service.QumuloAPI")
    def test_get_file_system_allocations_near_limit(
        self, qumulo_api_mock: MagicMock
    ) -> None:
        qumulo_api = MagicMock()
        qumulo_api.get_all_quotas_with_usage.return_value = self.mock_quota_response
        qumulo_api_mock.return_value = qumulo_api

        allocations_near_limit = (
            FileQuotaService.get_file_system_allocations_near_limit()
        )
        are_all_allocations_near_limit = all(
            int(quota["capacity_usage"]) / int(quota["limit"])
            > float(os.environ.get("ALLOCATION_LIMIT_THRESHOLD"))
            for quota in allocations_near_limit
        )
        self.assertTrue(are_all_allocations_near_limit)
