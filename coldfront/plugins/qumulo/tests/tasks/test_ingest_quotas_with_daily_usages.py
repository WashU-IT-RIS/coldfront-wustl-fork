from django.test import TestCase

from unittest.mock import patch, MagicMock
from unittest import skip

from coldfront.plugins.qumulo.tests.utils.mock_data import (
    build_models,
    create_allocation,
    get_mock_quota_data,
    get_mock_quota_base_allocations,
    get_mock_quota_sub_allocations,
    get_mock_quota_response,
    mock_qumulo_info,
    default_form_data,
)
from coldfront.plugins.qumulo.tasks import (
    ingest_quotas_with_daily_usage,
)
from coldfront.plugins.qumulo import tasks as qumulo_api

from coldfront.core.allocation.models import (
    AllocationAttribute,
    AllocationAttributeType,
)
from coldfront.core.test_helpers.factories import AllocationStatusChoiceFactory

import json


class TestIngestQuotasWithDailyUsages(TestCase):
    def setUp(self) -> None:
        patch.dict(
            "os.environ",
            {
                "QUMULO_INFO": json.dumps(mock_qumulo_info),
            },
        ).start()

        self.storage_path = list(mock_qumulo_info.values())[0]["path"]
        build_data = build_models()

        self.project = build_data["project"]
        self.user = build_data["user"]

        self.mock_quota_response = get_mock_quota_response(
            get_mock_quota_data(self.storage_path), self.storage_path
        )

        self.status_active = AllocationStatusChoiceFactory(name="Active")
        self.status_ready_for_deletion = AllocationStatusChoiceFactory(
            name="Ready for Deletion"
        )

        for index, (path, value) in enumerate(
            get_mock_quota_data(self.storage_path).items()
        ):
            form_data = default_form_data.copy()
            form_data_mods = {
                "storage_filesystem_path": path.rstrip("/"),
                "storage_export_path": path.rstrip("/"),
                "storage_name": f"for_tester_{index}",
                "storage_quota": value["limit"],
                "rw_users": [f"user_{index}_rw"],
                "ro_users": [f"user_{index}_ro"],
                "storage_ticket": f"ITSD-{index}",
            }
            form_data.update(form_data_mods)

            allocation = create_allocation(
                project=self.project, user=self.user, form_data=form_data
            )
            allocation.status = self.status_active
            allocation.save()

        self.storage_filesystem_path_attribute_type = (
            AllocationAttributeType.objects.get(name="storage_filesystem_path")
        )
        self.storage_quota_attribute_type = AllocationAttributeType.objects.get(
            name="storage_quota"
        )

        return super().setUp()

    def tearDown(self) -> None:
        patch.stopall()

        return super().tearDown()

    @patch.dict("os.environ", {"QUMULO_RESULT_SET_PAGE_LIMIT": "2000"})
    def test_qumulo_result_set_page_limit_should_be_set(self) -> None:
        page_limit = qumulo_api.QumuloAPI.get_result_set_page_limit()
        self.assertIsNotNone(page_limit)

    @skip("Until we have a chance to propagte the ENV variable.")
    @patch.dict("os.environ", {"QUMULO_RESULT_SET_PAGE_LIMIT": ""})
    def test_qumulo_result_set_page_limit_should_raise_an_exception_if_not_set(
        self,
    ) -> None:
        with self.assertRaises(TypeError):
            qumulo_api.QumuloAPI.get_result_set_page_limit()

    def test_after_allocation_create_usage_is_zero(self) -> None:
        for path in get_mock_quota_data(self.storage_path).keys():
            allocation_attribute_usage = None
            try:
                storage_filesystem_path_attribute = AllocationAttribute.objects.select_related(
                    "allocation"
                ).get(
                    value=path.rstrip("/"),
                    allocation_attribute_type=self.storage_filesystem_path_attribute_type,
                    allocation__status=self.status_active,
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
            self.assertEqual(allocation_attribute_usage.history.count(), 1)

    @patch(
        "coldfront.plugins.qumulo.utils.storage_controller.StorageControllerFactory.create_connection"
    )
    def test_after_getting_daily_usages_from_qumulo_api(
        self, create_connection_mock: MagicMock
    ) -> None:
        qumulo_api = MagicMock()
        qumulo_api.get_all_quotas_with_usage.return_value = self.mock_quota_response
        create_connection_mock.return_value = qumulo_api

        try:
            ingest_quotas_with_daily_usage()
        except:
            self.fail("Ingest quotas raised exception")

        base_quotas = get_mock_quota_base_allocations(self.storage_path)
        for path, quota_data in base_quotas.items():
            storage_filesystem_path_attribute = AllocationAttribute.objects.select_related(
                "allocation"
            ).get(
                value=path.rstrip("/"),
                allocation_attribute_type=self.storage_filesystem_path_attribute_type,
                allocation__status=self.status_active,
            )

            allocation = storage_filesystem_path_attribute.allocation
            storage_quota_attribute = AllocationAttribute.objects.get(
                allocation=allocation,
                allocation_attribute_type=self.storage_quota_attribute_type,
            )

            allocation_attribute_usage = (
                storage_quota_attribute.allocationattributeusage
            )

            usage = int(quota_data["usage"])
            self.assertEqual(allocation_attribute_usage.value, usage)
            self.assertEqual(allocation_attribute_usage.history.first().value, usage)
            self.assertGreater(allocation_attribute_usage.history.count(), 1)

    @patch(
        "coldfront.plugins.qumulo.utils.storage_controller.StorageControllerFactory.create_connection"
    )
    def test_doesnt_ingest_sub_allocation_data(
        self, create_connection_mock: MagicMock
    ) -> None:
        qumulo_api = MagicMock()
        qumulo_api.get_all_quotas_with_usage.return_value = self.mock_quota_response
        create_connection_mock.return_value = qumulo_api

        try:
            ingest_quotas_with_daily_usage()
        except:
            self.fail("Ingest quotas raised exception")

        sub_quotas = get_mock_quota_sub_allocations(self.storage_path)
        for path in sub_quotas.keys():
            allocation_attribute_usage = None
            storage_filesystem_path_attribute = AllocationAttribute.objects.get(
                value=path.rstrip("/"),
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

            self.assertEqual(allocation_attribute_usage.value, 0)
            self.assertEqual(allocation_attribute_usage.history.count(), 1)

    @patch(
        "coldfront.plugins.qumulo.utils.storage_controller.StorageControllerFactory.create_connection"
    )
    def test_filtering_out_not_active_allocations(
        self, create_connection_mock: MagicMock
    ) -> None:
        index = 1
        path = f"{self.storage_path}/status_test"
        limit = "100000000000000"
        capacity_usage = "37089837494272"

        mock_quota = {
            "quotas": [
                {
                    "id": index,
                    "path": path,
                    "limit": limit,
                    "capacity_usage": capacity_usage,
                }
            ],
            "paging": {"next": ""},
        }

        qumulo_api = MagicMock()
        qumulo_api.get_all_quotas_with_usage.return_value = mock_quota
        create_connection_mock.return_value = qumulo_api

        form_data = default_form_data.copy()
        form_data_mods = {
            "storage_filesystem_path": path,
            "storage_export_path": path,
            "storage_name": f"for_tester_{index}",
            "storage_quota": limit,
            "rw_users": [f"user_{index}_rw"],
            "ro_users": [f"user_{index}_ro"],
            "storage_ticket": f"ITSD-{index}",
        }
        form_data.update(form_data_mods)

        allocation_active = create_allocation(
            project=self.project, user=self.user, form_data=form_data
        )
        allocation_active.status = self.status_active
        allocation_active.save()

        allocation_ready_for_deletion = create_allocation(
            project=self.project, user=self.user, form_data=form_data
        )
        allocation_ready_for_deletion.status = self.status_ready_for_deletion
        allocation_ready_for_deletion.save()

        try:
            ingest_quotas_with_daily_usage()
        except:
            self.fail("ingest_quotas failed")

        storage_filesystem_path_attribute = AllocationAttribute.objects.select_related(
            "allocation"
        ).get(
            value=path,
            allocation_attribute_type=self.storage_filesystem_path_attribute_type,
            allocation__status=self.status_active,
        )
        active_allocation = storage_filesystem_path_attribute.allocation

        self.assertEqual(active_allocation.status, self.status_active)

        storage_quota_attribute = AllocationAttribute.objects.get(
            allocation=active_allocation,
            allocation_attribute_type=self.storage_quota_attribute_type,
        )
        allocation_attribute_usage = storage_quota_attribute.allocationattributeusage
        usage = int(capacity_usage)

        self.assertEqual(allocation_attribute_usage.value, usage)
        self.assertEqual(allocation_attribute_usage.history.first().value, usage)
        self.assertGreater(allocation_attribute_usage.history.count(), 1)
