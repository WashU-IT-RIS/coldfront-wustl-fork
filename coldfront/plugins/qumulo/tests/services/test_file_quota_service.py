import os
from dotenv import load_dotenv

from coldfront.plugins.qumulo.tests.fixtures import create_metadata_for_testing

from coldfront.plugins.qumulo.tests.utils.mock_data import get_mock_quota_response

load_dotenv(override=True)

from django.test import TestCase

from unittest.mock import patch, MagicMock

from coldfront.plugins.qumulo.services.file_quota_service import FileQuotaService


class TestFileQuotaService(TestCase):

    def setUp(self):
        create_metadata_for_testing()
        self.mock_quota_allocations = {
            f"/storage2-dev/fs1/near_limit/": {
                "id": "42080003",
                "limit": "38482906972160",
                "usage": "36558761623552",
            },
            f"/storage2-dev/fs1/over_limit/": {
                "id": "42130003",
                "limit": "5497558138880",
                "usage": "6497558138880",
            },
            f"/storage2-dev/fs1/under_limit/": {
                "id": "52929567",
                "limit": "16492674416640",
                "usage": "997732352",
            },
            f"/storage2-dev/fs1/just_inside_near_limit/": {
                "id": "43010005",
                "limit": "109951162777600",
                "usage": "98956046499840",
            },
            f"/storage2-dev/fs1/at_the_limit/": {
                "id": "42030003",
                "limit": "38482906972160",
                "usage": "38482906972160",
            },
        }
        self.mock_quota_response = get_mock_quota_response(
            self.mock_quota_allocations, "/storage2-dev/fs1/"
        )
        self.qumulo_api = MagicMock()
        self.qumulo_api.get_all_quotas_with_usage.return_value = (
            self.mock_quota_response
        )
        return super().setUp()

    @patch.dict(os.environ, {"QUMULO_RESULT_SET_PAGE_LIMIT": "2000"})
    @patch.dict(os.environ, {"ALLOCATION_LIMIT_THRESHOLD": "0.9"})
    @patch("coldfront.plugins.qumulo.services.file_quota_service.QumuloAPI")
    def test_get_file_system_allocations_near_limit(
        self, qumulo_api_mock: MagicMock
    ) -> None:
        qumulo_api_mock.return_value = self.qumulo_api
        allocations_near_limit = (
            FileQuotaService.get_file_system_allocations_near_limit()
        )

        are_all_allocations_near_limit = all(
            int(quota["capacity_usage"]) / int(quota["limit"])
            >= float(os.environ.get("ALLOCATION_LIMIT_THRESHOLD"))
            for quota in allocations_near_limit
        )
        self.assertEqual(
            len(self.mock_quota_allocations), 5, "Expects QUMULO to have 5 allocations"
        )
        self.assertEqual(
            len(allocations_near_limit),
            4,
            "Expects to find 4 allocations near or over the limit",
        )
        self.assertTrue(
            are_all_allocations_near_limit,
            "Expects the result to have all allocations near or over the limit",
        )
