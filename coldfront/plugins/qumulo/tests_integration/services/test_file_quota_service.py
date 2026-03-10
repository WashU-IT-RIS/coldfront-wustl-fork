import os
from dotenv import load_dotenv

load_dotenv(override=True)

from django.test import TestCase, tag

from unittest import mock

from coldfront.plugins.qumulo.services.file_quota_service import FileQuotaService


class TestFileQuotaService(TestCase):

    @mock.patch.dict(os.environ, {"QUMULO_RESULT_SET_PAGE_LIMIT": "2000"})
    @mock.patch.dict(os.environ, {"ALLOCATION_NEAR_LIMIT_THRESHOLD": "0.9"})
    @tag("integration")
    def test_file_system_allocations_near_limit(self):
        allocations_near_limit = (
            FileQuotaService.get_file_system_allocations_near_limit()
        )
        are_all_allocations_near_limit = all(
            int(quota["capacity_usage"]) / int(quota["limit"])
            > float(os.environ.get("ALLOCATION_NEAR_LIMIT_THRESHOLD"))
            for quota in allocations_near_limit
        )
        self.assertTrue(are_all_allocations_near_limit)
