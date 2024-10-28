from django.test import TestCase, Client

from unittest.mock import patch, MagicMock

from coldfront.plugins.qumulo.tests.utils.mock_data import (
    build_models,
    create_allocation,
    mock_quota_data,
)
from coldfront.plugins.qumulo.tasks import (
    poll_ad_group,
    poll_ad_groups,
    conditionally_update_storage_allocation_status,
    conditionally_update_storage_allocation_statuses,
    ingest_quotas_with_daily_usage,
)
from coldfront.plugins.qumulo.utils.acl_allocations import AclAllocations

from coldfront.core.allocation.models import (
    Allocation,
    AllocationStatusChoice,
    AllocationAttribute,
    AllocationAttributeType,
)

from coldfront.core.resource.models import Resource

from qumulo.lib.request import RequestError

import datetime
from django.utils import timezone


@patch("coldfront.plugins.qumulo.tasks.QumuloAPI")
class TestPollAdGroup(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        build_data = build_models()

        self.project = build_data["project"]
        self.user = build_data["user"]

        return super().setUp()

    def test_poll_ad_group_set_status_to_active_on_success(
        self, qumulo_api_mock: MagicMock
    ) -> None:

        acl_allocation: Allocation = Allocation.objects.create(
            project=self.project,
            justification="",
            quantity=1,
            status=AllocationStatusChoice.objects.get_or_create(name="Pending")[0],
        )

        poll_ad_group(acl_allocation=acl_allocation)

        self.assertEqual(acl_allocation.status.name, "Active")

    def test_poll_ad_group_set_status_does_nothing_on_failure(
        self, qumulo_api_mock: MagicMock
    ) -> None:
        acl_allocation: Allocation = Allocation.objects.create(
            project=self.project,
            justification="",
            quantity=1,
            status=AllocationStatusChoice.objects.get_or_create(name="Pending")[0],
        )

        get_ad_object_mock: MagicMock = (
            qumulo_api_mock.return_value.rc.ad.distinguished_name_to_ad_account
        )
        get_ad_object_mock.side_effect = [
            RequestError(status_code=404, status_message="Not found"),
        ]

        poll_ad_group(acl_allocation=acl_allocation)

        self.assertEqual(acl_allocation.status.name, "Pending")

    def test_poll_ad_group_set_status_to_denied_on_expiration(
        self, qumulo_api_mock: MagicMock
    ) -> None:
        acl_allocation: Allocation = Allocation.objects.create(
            project=self.project,
            justification="",
            quantity=1,
            status=AllocationStatusChoice.objects.get_or_create(name="Pending")[0],
            created=timezone.now() - datetime.timedelta(hours=2),
        )

        get_ad_object_mock: MagicMock = (
            qumulo_api_mock.return_value.rc.ad.distinguished_name_to_ad_account
        )
        get_ad_object_mock.side_effect = [
            RequestError(status_code=404, status_message="Not found"),
        ]

        poll_ad_group(
            acl_allocation=acl_allocation,
            expiration_seconds=60 * 60,
        )

        self.assertEqual(acl_allocation.status.name, "Expired")


@patch("coldfront.plugins.qumulo.tasks.QumuloAPI")
class TestPollAdGroups(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        build_data = build_models()

        self.project = build_data["project"]
        self.user = build_data["user"]

        return super().setUp()

    def test_poll_ad_groups_runs_poll_ad_group_for_each_pending_allocation(
        self, qumulo_api_mock: MagicMock
    ) -> None:
        acl_allocation_a: Allocation = Allocation.objects.create(
            project=self.project,
            justification="",
            quantity=1,
            status=AllocationStatusChoice.objects.get_or_create(name="Pending")[0],
        )
        resource_a = Resource.objects.get(name="rw")
        acl_allocation_a.resources.add(resource_a)

        acl_allocation_b: Allocation = Allocation.objects.create(
            project=self.project,
            justification="",
            quantity=1,
            status=AllocationStatusChoice.objects.get_or_create(name="Pending")[0],
        )
        resource_b = Resource.objects.get(name="ro")
        acl_allocation_b.resources.add(resource_b)

        acl_allocation_c: Allocation = Allocation.objects.create(
            project=self.project,
            justification="",
            quantity=1,
            status=AllocationStatusChoice.objects.get_or_create(name="New")[0],
        )
        acl_allocation_c.resources.add(resource_b)

        with patch(
            "coldfront.plugins.qumulo.tasks.poll_ad_group"
        ) as poll_ad_group_mock:
            poll_ad_groups()

            self.assertEqual(poll_ad_group_mock.call_count, 2)


class TestUpdateStorageAllocationPendingStatus(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        build_data = build_models()

        self.project = build_data["project"]
        self.user = build_data["user"]
        self.form_data = {
            "storage_filesystem_path": "foo",
            "storage_export_path": "bar",
            "storage_ticket": "ITSD-54321",
            "storage_name": "baz",
            "storage_quota": 7,
            "protocols": ["nfs"],
            "rw_users": ["test"],
            "ro_users": ["test1"],
            "cost_center": "Uncle Pennybags",
            "department_number": "Time Travel Services",
            "service_rate": "general",
        }

        return super().setUp()

    def test_conditionally_update_storage_allocation_status_sets_status_to_new_on_success(
        self,
    ) -> None:
        allocation = create_allocation(
            project=self.project, user=self.user, form_data=self.form_data
        )

        conditionally_update_storage_allocation_status(allocation)

        got_allocation = Allocation.objects.get(pk=allocation.pk)

        self.assertEqual(got_allocation.status.name, "New")

    def test_conditionally_update_storage_allocation_status_does_nothing_when_acls_are_pending(
        self,
    ) -> None:
        allocation = create_allocation(
            project=self.project, user=self.user, form_data=self.form_data
        )
        acl_allocation = AclAllocations.get_access_allocation(
            storage_allocation=allocation, resource_name="ro"
        )

        acl_allocation.status = AllocationStatusChoice.objects.get(name="Pending")
        acl_allocation.save()

        conditionally_update_storage_allocation_status(allocation)

        got_allocation = Allocation.objects.get(pk=allocation.pk)

        self.assertEqual(got_allocation.status.name, "Pending")


class TestStorageAllocationStatuses(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        build_data = build_models()

        self.project = build_data["project"]
        self.user = build_data["user"]
        self.form_data = {
            "storage_filesystem_path": "foo",
            "storage_export_path": "bar",
            "storage_ticket": "ITSD-54321",
            "storage_name": "baz",
            "storage_quota": 7,
            "protocols": ["nfs"],
            "rw_users": ["test"],
            "ro_users": ["test1"],
            "cost_center": "Uncle Pennybags",
            "department_number": "Time Travel Services",
            "service_rate": "general",
        }

        return super().setUp()

    def test_conditionally_update_storage_allocation_statuses_checks_all_pending_allocations(
        self,
    ):
        create_allocation(
            project=self.project, user=self.user, form_data=self.form_data
        )
        create_allocation(
            project=self.project, user=self.user, form_data=self.form_data
        )

        non_pending_allocation = create_allocation(
            project=self.project, user=self.user, form_data=self.form_data
        )
        non_pending_allocation.status = AllocationStatusChoice.objects.get(name="New")
        non_pending_allocation.save()

        with patch(
            "coldfront.plugins.qumulo.tasks.conditionally_update_storage_allocation_status"
        ) as conditionally_update_storage_allocation_status_mock:
            conditionally_update_storage_allocation_statuses()

            self.assertEqual(
                conditionally_update_storage_allocation_status_mock.call_count, 2
            )


class TestIngestQuotasWithDailyUsages(TestCase):
    def setUp(self) -> None:

        self.client = Client()
        build_data = build_models()

        self.project = build_data["project"]
        self.user = build_data["user"]

        quotas = list(
            map(
                lambda quota_key_value: (
                    {
                        "id": quota_key_value[1]["id"],
                        "path": quota_key_value[0],
                        "limit": quota_key_value[1]["limit"],
                        "capacity_usage": quota_key_value[1]["usage"],
                    }
                ),
                mock_quota_data.items(),
            )
        )
        self.quotas = {"quotas": quotas, "paging": {"next": ""}}

        for index, (path, value) in enumerate(mock_quota_data.items()):
            if "exclude" in path:
                continue

            form_data = {
                "storage_filesystem_path": path,
                "storage_export_path": path,
                "storage_name": f"for_tester_{index}",
                "storage_quota": value["limit"],
                "protocols": ["nfs"],
                "rw_users": [f"user_{index}_rw"],
                "ro_users": [f"user_{index}_ro"],
                "storage_ticket": f"ITSD-{index}",
                "cost_center": "Uncle Pennybags",
                "department_number": "Time Travel Services",
                "service_rate": "general",
            }

            create_allocation(project=self.project, user=self.user, form_data=form_data)

        self.storage_filesystem_path_attribute_type = (
            AllocationAttributeType.objects.get(name="storage_filesystem_path")
        )
        self.storage_quota_attribute_type = AllocationAttributeType.objects.get(
            name="storage_quota"
        )

        return super().setUp()

    def test_after_allocation_create_usage_is_zero(self) -> None:
        for path in mock_quota_data.keys():
            if "exclude" in path:
                continue

            allocation_attribute_usage = None
            try:
                storage_filesystem_path_attribute = AllocationAttribute.objects.get(
                    value=path,
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

    @patch("coldfront.plugins.qumulo.tasks.QumuloAPI")
    def test_after_getting_daily_usages_from_qumulo_api(
        self, qumulo_api_mock: MagicMock
    ) -> None:
        qumulo_api = MagicMock()
        qumulo_api.get_all_quotas_with_usage.return_value = self.quotas
        qumulo_api_mock.return_value = qumulo_api

        try:
            ingest_quotas_with_daily_usage()
        except:
            self.fail("Ingest quotas raised exception")

        for qumulo_quota in self.quotas["quotas"]:
            allocation_attribute_usage = None
            storage_filesystem_path_attribute = AllocationAttribute.objects.get(
                value=qumulo_quota["path"],
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

            usage = int(qumulo_quota.get("capacity_usage"))
            self.assertEqual(allocation_attribute_usage.value, usage)
            self.assertEqual(
                allocation_attribute_usage.history.first().value,
                usage,
            )
