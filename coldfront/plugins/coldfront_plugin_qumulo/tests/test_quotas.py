from venv import logger
from django.test import TestCase, Client

from unittest.mock import patch, MagicMock

from coldfront.core.allocation.models import (
    AllocationAttribute,
    AllocationAttributeType,
)
from coldfront_plugin_qumulo.tasks import ingest_quotas_with_daily_usage
from coldfront_plugin_qumulo.tests.utils.mock_data import (
    build_models,
    create_allocation,
)

from qumulo.lib.request import RequestError


def mock_get_quotas() -> str:
    return {
        "quotas": [
            {
                "id": "2020003",
                "path": "/storage2-dev/fs1/tic/",
                "limit": "1000000000000",
                "capacity_usage": "999999999",
            },
            {
                "id": "2060005",
                "path": "/storage2-dev/fs1/tac/",
                "limit": "1000000000000",
                "capacity_usage": "100000000",
            },
            {
                "id": "2410003",
                "path": "/storage2-dev/fs1/toe/",
                "limit": "500000000000",
                "capacity_usage": "500000000000",
            },
            {
                "id": "2410003",
                "path": "/storage2-dev/fs1/not_found/",
                "limit": "500000000000",
                "capacity_usage": "500000000000",
            },
        ],
        "paging": {"next": ""},
    }


class TestIngestAllocationDailyUsages(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        build_data = build_models()

        self.project = build_data["project"]
        self.user = build_data["user"]

        wustl_keys = ["tic", "tac", "toe"]
        for key in wustl_keys:
            form_data = {
                "storage_filesystem_path": f"/storage2-dev/fs1/{key}/",
                "storage_export_path": f"/storage2-dev/fs1/{key}/",
                "storage_name": f"for_tester_{key}",
                "storage_quota": 10,
                "protocols": ["nfs"],
                "rw_users": [key],
                "ro_users": [key],
            }
            create_allocation(project=self.project, user=self.user, form_data=form_data)
            self.quotas = mock_get_quotas()
            self.storage_filesystem_path_attribute_type = (
                AllocationAttributeType.objects.get(name="storage_filesystem_path")
            )
            self.storage_quota_attribute_type = AllocationAttributeType.objects.get(
                name="storage_quota"
            )

        return super().setUp()

    def test_after_allocation_create_usage_is_zero(self) -> None:

        # after allocations are created, expect usage to be zero
        for quote in self.quotas["quotas"]:
            allocation_attribute_usage = None
            try:
                storage_filesystem_path_attribute = AllocationAttribute.objects.get(
                    value=quote["path"],
                    allocation_attribute_type=self.storage_filesystem_path_attribute_type,
                )
                allocation = storage_filesystem_path_attribute.allocation
                storage_quota_attribute_type = AllocationAttribute.objects.get(
                    allocation=allocation,
                    allocation_attribute_type=self.storage_quota_attribute_type,
                )
                allocation_attribute_usage = (
                    storage_quota_attribute_type.allocationattributeusage
                )
            except AllocationAttribute.DoesNotExist:
                # When the storage_path_attribute for path is not found,
                # the allocation_attribute_usage should not exist.
                self.assertIsNone(allocation_attribute_usage)
                continue

            self.assertEqual(allocation_attribute_usage.value, 0)
            self.assertEqual(allocation_attribute_usage.history.first().value, 0)

    @patch("coldfront_plugin_qumulo.tasks.QumuloAPI")
    def test_after_getting_daily_usages_from_qumulo_api(
        self, qumulo_api_mock: MagicMock
    ) -> None:
        qumulo_api = MagicMock()
        qumulo_api.get_all_quotas_with_usage.return_value = mock_get_quotas()
        qumulo_api_mock.return_value = qumulo_api

        exceptionRaised = False
        try:
            ingest_quotas_with_daily_usage()
        except:
            exceptionRaised = True

        self.assertFalse(exceptionRaised)

        for quota in self.quotas["quotas"]:

            allocation_attribute_usage = None
            try:
                storage_filesystem_path_attribute = AllocationAttribute.objects.get(
                    value=quota["path"],
                    allocation_attribute_type=self.storage_filesystem_path_attribute_type,
                )
                allocation = storage_filesystem_path_attribute.allocation
                storage_quota_attribute = AllocationAttribute.objects.get(
                    allocation=allocation,
                    allocation_attribute_type=self.storage_quota_attribute_type,
                )
                allocation_attribute_usage = (
                    storage_quota_attribute.allocationattributeusage
                )
            except AllocationAttribute.DoesNotExist:
                # When the storage_path_attribute for path is not found,
                # the allocation_attribute_usage should not exist.
                self.assertIsNone(allocation_attribute_usage)
                continue

            self.assertEqual(
                allocation_attribute_usage.value, int(quota["capacity_usage"])
            )
            self.assertEqual(
                allocation_attribute_usage.history.first().value,
                int(quota["capacity_usage"]),
            )
