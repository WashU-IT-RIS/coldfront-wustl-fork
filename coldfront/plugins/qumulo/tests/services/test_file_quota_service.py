import os
from dotenv import load_dotenv

from coldfront.plugins.qumulo.tests.fixtures import create_allocation_assets

load_dotenv(override=True)

from django.test import TestCase

from unittest import mock

from coldfront.plugins.qumulo.services.file_quota_service import FileQuotaService

from coldfront.plugins.qumulo.tests.helper_classes.factories import (
    RISAllocationFactory,
    RISProjectFactory,
    Storage2Factory,
    ReadOnlyGroupFactory,
    ReadWriteGroupFactory,
)


class TestFileQuotaService(TestCase):

    def setUp(self):
        create_allocation_assets()
        return super().setUp()

    @mock.patch.dict(os.environ, {"QUMULO_RESULT_SET_PAGE_LIMIT": "2000"})
    @mock.patch.dict(os.environ, {"ALLOCATION_LIMIT_THRESHOLD": "0.000000001"})
    def test_get_file_system_allocations_near_limit(self):
        breakpoint()
        allocations_near_limit = (
            FileQuotaService.get_file_system_allocations_near_limit()
        )
        are_all_allocations_near_limit = all(
            int(quota["capacity_usage"]) / int(quota["limit"])
            > float(os.environ.get("ALLOCATION_LIMIT_THRESHOLD"))
            for quota in allocations_near_limit
        )
        self.assertTrue(are_all_allocations_near_limit)
