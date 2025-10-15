from django.test import TestCase, Client

from unittest.mock import patch, MagicMock, ANY
from django.utils import timezone

from unittest.mock import patch, MagicMock

from coldfront.plugins.qumulo.tests.utils.mock_data import (
    build_models,
    mock_qumulo_info,
    create_allocation,
    default_form_data,
)
from coldfront.plugins.qumulo.tasks import (
    poll_ad_group,
)
from coldfront.core.allocation.models import (
    Allocation,
    AllocationStatusChoice,
)

from coldfront.plugins.qumulo.utils.acl_allocations import AclAllocations

from qumulo.lib.request import RequestError

import datetime
import json


@patch(
    "coldfront.plugins.qumulo.utils.storage_controller.StorageControllerFactory.create_connection"
)
class TestPollAdGroup(TestCase):
    def setUp(self) -> None:
        patch.dict(
            "os.environ",
            {
                "QUMULO_INFO": json.dumps(mock_qumulo_info),
            },
        ).start()

        self.client = Client()
        build_data = build_models()

        self.project = build_data["project"]
        self.user = build_data["user"]

        self.storage_allocation = create_allocation(
            self.project, self.user, default_form_data
        )

        return super().setUp()

    def tearDown(self):
        patch.stopall()

        return super().tearDown()

    def test_poll_ad_group_set_status_to_active_on_success(
        self, create_connection_mock: MagicMock
    ) -> None:
        acl_allocation = AclAllocations.get_access_allocation(
            self.storage_allocation, "rw"
        )
        acl_allocation.status = AllocationStatusChoice.objects.get_or_create(
            name="Pending"
        )[0]
        acl_allocation.save()

        poll_ad_group(acl_allocation=acl_allocation)

        self.assertEqual(acl_allocation.status.name, "Active")

    def test_poll_ad_group_set_status_does_nothing_on_failure(
        self, create_connection_mock: MagicMock
    ) -> None:
        acl_allocation = AclAllocations.get_access_allocation(
            self.storage_allocation, "rw"
        )
        acl_allocation.status = AllocationStatusChoice.objects.get_or_create(
            name="Pending"
        )[0]
        acl_allocation.save()

        get_ad_object_mock: MagicMock = (
            create_connection_mock.return_value.rc.ad.distinguished_name_to_ad_account
        )
        get_ad_object_mock.side_effect = [
            RequestError(status_code=404, status_message="Not found"),
        ]

        poll_ad_group(acl_allocation=acl_allocation)

        self.assertEqual(acl_allocation.status.name, "Pending")

    def test_poll_ad_group_set_status_to_denied_on_expiration(
        self, create_connection_mock: MagicMock
    ) -> None:
        acl_allocation = AclAllocations.get_access_allocation(
            self.storage_allocation, "rw"
        )
        acl_allocation.status = AllocationStatusChoice.objects.get_or_create(
            name="Pending"
        )[0]
        acl_allocation.created = timezone.now() - datetime.timedelta(hours=2)
        acl_allocation.save()

        get_ad_object_mock: MagicMock = (
            create_connection_mock.return_value.rc.ad.distinguished_name_to_ad_account
        )
        get_ad_object_mock.side_effect = [
            RequestError(status_code=404, status_message="Not found"),
        ]

        poll_ad_group(
            acl_allocation=acl_allocation,
            expiration_seconds=60 * 60,
        )

        self.assertEqual(acl_allocation.status.name, "Expired")
