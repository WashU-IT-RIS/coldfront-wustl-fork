import os
from dotenv import load_dotenv

from formencode.validators import Email

from coldfront.core.utils.mail import allocation_email_recipients
from coldfront.plugins.qumulo.services.notifications_service import (
    send_email_for_near_limit_allocation,
)
from coldfront.plugins.qumulo.tasks import notify_users_with_allocations_near_limit
from coldfront.plugins.qumulo.tests.fixtures import (
    create_metadata_for_testing,
    create_ris_project_and_allocations_storage2,
)

from coldfront.plugins.qumulo.tests.utils.mock_data import get_mock_quota_response
from coldfront.plugins.qumulo.utils.mail import allocation_user_recipients_for_ris

load_dotenv(override=True)

from django.test import TestCase

from unittest.mock import patch, MagicMock

from coldfront.plugins.qumulo.services.file_quota_service import FileQuotaService


@patch.dict(os.environ, {"QUMULO_RESULT_SET_PAGE_LIMIT": "2000"})
@patch.dict(os.environ, {"ALLOCATION_NEAR_LIMIT_THRESHOLD": "0.9"})
class TestFileQuotaService(TestCase):

    def setUp(self):
        create_metadata_for_testing()
        storage_path = os.environ.get("STORAGE2_PATH").rstrip("/")
        self.mock_quota_allocations = [
            {
                "path": f"{storage_path}/near_limit",
                "id": "42080003",
                "limit": "38482906972160",
                "capacity_usage": "36558761623552",
            },
            {
                "path": f"{storage_path}/over_limit",
                "id": "42130003",
                "limit": "5497558138880",
                "capacity_usage": "6497558138880",
            },
            {
                "path": f"{storage_path}/under_limit",
                "id": "52929567",
                "limit": "16492674416640",
                "capacity_usage": "997732352",
            },
            {
                "path": f"{storage_path}/just_inside_near_limit",
                "id": "43010005",
                "limit": "109951162777600",
                "capacity_usage": "98956046499840",
            },
            {
                "path": f"{storage_path}/at_the_limit",
                "id": "42030003",
                "limit": "38482906972160",
                "capacity_usage": "38482906972160",
            },
        ]
        self.qumulo_api = MagicMock()
        self.qumulo_api.get_all_quotas_with_usage.return_value = {
            "quotas": self.mock_quota_allocations,
            "paging": {"next": ""},
        }
        return super().setUp()

    @patch(
        "coldfront.plugins.qumulo.utils.storage_controller.StorageControllerFactory.create_connection"
    )
    def test_get_file_system_allocations_near_limit(
        self, create_connection_mock: MagicMock
    ) -> None:
        create_connection_mock.return_value = self.qumulo_api
        allocations_near_limit = (
            FileQuotaService.get_file_system_allocations_near_limit()
        )

        are_all_allocations_near_limit = all(
            int(quota["capacity_usage"]) / int(quota["limit"])
            >= float(os.environ.get("ALLOCATION_NEAR_LIMIT_THRESHOLD"))
            for quota in allocations_near_limit
        )

        self.assertEqual(
            len(self.mock_quota_allocations), 5, "Expects QUMULO to have 5 allocations"
        )
        breakpoint()
        self.assertEqual(
            len(allocations_near_limit),
            4,
            "Expects to find 4 allocations near or over the limit",
        )
        self.assertTrue(
            are_all_allocations_near_limit,
            "Expects the result to have all allocations near or over the limit",
        )

    @patch(
        "coldfront.plugins.qumulo.utils.storage_controller.StorageControllerFactory.create_connection"
    )
    def test_create_email_receiver_list(self, qumulo_api_mock: MagicMock) -> None:
        qumulo_api_mock.return_value = self.qumulo_api
        allocations_near_limit = (
            FileQuotaService.get_file_system_allocations_near_limit()
        )
        for quota in allocations_near_limit:
            project, _ = create_ris_project_and_allocations_storage2(path=quota["path"])
            recipients = allocation_user_recipients_for_ris(project)
            self.assertIsInstance(recipients, list)
            self.assertTrue(all(Email.to_python(email) for email in recipients))

    @patch(
        "coldfront.plugins.qumulo.utils.storage_controller.StorageControllerFactory.create_connection"
    )
    def test_send_email_for_allocations_near_limit(self, qumulo_api_mock: MagicMock):
        qumulo_api_mock.return_value = self.qumulo_api
        allocations_near_limit = (
            FileQuotaService.get_file_system_allocations_near_limit()
        )
        for quota in allocations_near_limit:
            project, _ = create_ris_project_and_allocations_storage2(path=quota["path"])
            recipients = allocation_user_recipients_for_ris(project)
            self.assertIsInstance(recipients, list)
            self.assertTrue(all(Email.to_python(recipient) for recipient in recipients))

    @patch(
        "coldfront.plugins.qumulo.utils.storage_controller.StorageControllerFactory.create_connection"
    )
    def test_notify_users_with_allocations_near_limit_task(
        self, qumulo_api_mock: MagicMock
    ):
        qumulo_api_mock.return_value = self.qumulo_api
        allocations_near_limit = (
            FileQuotaService.get_file_system_allocations_near_limit()
        )
        for quota in allocations_near_limit:
            project, _ = create_ris_project_and_allocations_storage2(path=quota["path"])

        notify_users_with_allocations_near_limit()
