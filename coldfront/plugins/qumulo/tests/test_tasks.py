from django.test import TestCase, Client

from unittest.mock import patch, MagicMock

from coldfront.plugins.qumulo.tests.utils.mock_data import (
    build_models,
    create_allocation,
    enumerate_directory_contents,
)
from coldfront.plugins.qumulo.tasks import (
    poll_ad_group,
    poll_ad_groups,
    conditionally_update_storage_allocation_status,
    conditionally_update_storage_allocation_statuses,
    addUsersToADGroup,
    ResetAcl,
)
from coldfront.plugins.qumulo.utils.acl_allocations import AclAllocations
from coldfront.plugins.qumulo.views.allocation_view import AllocationView

from coldfront.core.allocation.models import (
    Allocation,
    AllocationStatusChoice,
    AllocationUser,
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


@patch("coldfront.plugins.qumulo.views.allocation_view.async_task")
@patch("coldfront.plugins.qumulo.views.allocation_view.ActiveDirectoryAPI")
@patch("coldfront.plugins.qumulo.tasks.async_task")
@patch("coldfront.plugins.qumulo.tasks.ActiveDirectoryAPI")
class TestAddUsersToADGroup(TestCase):
    def setUp(self) -> None:
        self.client = Client()

        build_data = build_models()

        self.project = build_data["project"]
        self.user = build_data["user"]

        self.form_data = {
            "project_pk": self.project.id,
            "storage_filesystem_path": "foo",
            "storage_export_path": "bar",
            "storage_ticket": "ITSD-54321",
            "storage_name": "baz",
            "storage_quota": 7,
            "protocols": ["nfs"],
            "rw_users": ["foo"],
            "ro_users": ["test1"],
            "cost_center": "Uncle Pennybags",
            "department_number": "Time Travel Services",
            "service_rate": "general",
        }

        self.client.force_login(self.user)

        self.create_allocation = AllocationView.create_new_allocation

        return super().setUp()

    def test_function_ends_on_empty_list(
        self,
        mock_active_directory_api: MagicMock,
        mock_async_task: MagicMock,
        mock_allocation_view_AD: MagicMock,
        mock_allocation_view_async_task,
    ):
        wustlkeys = []
        self.form_data["ro_users"] = wustlkeys

        allocation = self.create_allocation(user=self.user, form_data=self.form_data)[
            "allocation"
        ]
        acl_allocation = AclAllocations.get_access_allocation(
            storage_allocation=allocation, resource_name="ro"
        )

        try:
            addUsersToADGroup([], acl_allocation)
        except Exception as e:
            self.fail("Function failed with exception: " + e)

    def test_checks_first_user_in_list(
        self,
        mock_active_directory_api: MagicMock,
        mock_async_task: MagicMock,
        mock_allocation_view_AD: MagicMock,
        mock_allocation_view_async_task,
    ):
        active_directory_instance = MagicMock()
        mock_active_directory_api.return_value = active_directory_instance

        wustlkeys = ["foo"]
        self.form_data["rw_users"] = wustlkeys

        allocation = self.create_allocation(user=self.user, form_data=self.form_data)[
            "allocation"
        ]
        acl_allocation = AclAllocations.get_access_allocation(
            storage_allocation=allocation, resource_name="rw"
        )

        addUsersToADGroup(wustlkeys, acl_allocation)

        active_directory_instance.get_user.assert_called_once_with(wustlkeys[0])

    def test_adds_user_to_group_after_check(
        self,
        mock_active_directory_api: MagicMock,
        mock_async_task: MagicMock,
        mock_allocation_view_AD: MagicMock,
        mock_allocation_view_async_task,
    ):
        active_directory_instance = MagicMock()
        mock_active_directory_api.return_value = active_directory_instance

        wustlkeys = ["foo"]
        self.form_data["rw_users"] = wustlkeys

        allocation = self.create_allocation(user=self.user, form_data=self.form_data)[
            "allocation"
        ]
        acl_allocation = AclAllocations.get_access_allocation(
            storage_allocation=allocation, resource_name="rw"
        )
        group_name = acl_allocation.get_attribute("storage_acl_name")

        addUsersToADGroup(wustlkeys, acl_allocation)

        active_directory_instance.add_user_to_ad_group.assert_called_once_with(
            wustlkeys[0], group_name
        )

    def test_adds_new_task_with_sliced_list(
        self,
        mock_active_directory_api: MagicMock,
        mock_async_task: MagicMock,
        mock_allocation_view_AD: MagicMock,
        mock_allocation_view_async_task,
    ):
        wustlkeys = ["foo", "bar"]
        self.form_data["rw_users"] = wustlkeys

        allocation = self.create_allocation(user=self.user, form_data=self.form_data)[
            "allocation"
        ]
        acl_allocation = AclAllocations.get_access_allocation(
            storage_allocation=allocation, resource_name="rw"
        )

        addUsersToADGroup(wustlkeys, acl_allocation)

        mock_async_task.assert_called_once()
        self.assertTupleEqual(
            mock_async_task.call_args[0],
            (addUsersToADGroup, (["bar"], acl_allocation, [])),
        )

    def test_appends_bad_user_list_on_invalid_user(
        self,
        mock_active_directory_api: MagicMock,
        mock_async_task: MagicMock,
        mock_allocation_view_AD: MagicMock,
        mock_allocation_view_async_task,
    ):
        active_directory_instance = MagicMock()
        active_directory_instance.get_user.side_effect = ValueError("Invalid wustlkey")
        mock_active_directory_api.return_value = active_directory_instance

        wustlkeys = ["foo", "bar"]
        self.form_data["rw_users"] = wustlkeys

        allocation = self.create_allocation(user=self.user, form_data=self.form_data)[
            "allocation"
        ]
        acl_allocation = AclAllocations.get_access_allocation(
            storage_allocation=allocation, resource_name="rw"
        )

        addUsersToADGroup(wustlkeys, acl_allocation)

        mock_async_task.assert_called_once()
        self.assertTupleEqual(
            mock_async_task.call_args[0],
            (addUsersToADGroup, (["bar"], acl_allocation, ["foo"])),
        )

    # def test_removes_bad_users_on_completion(
    #     self,
    #     mock_active_directory_api: MagicMock,
    #     mock_async_task: MagicMock,
    #     mock_allocation_view_AD: MagicMock,
    #     mock_allocation_view_async_task,
    # ):
    #     mock_async_task.side_effect = lambda *args: args[0](*args[1])

    #     wustlkeys = ["foo", "bar", "baz"]
    #     good_keys = wustlkeys[0:1]

    #     active_directory_instance = MagicMock()
    #     active_directory_instance.get_user.side_effect = (
    #         lambda username: self.__get_user_mock(username, good_keys)
    #     )
    #     mock_active_directory_api.return_value = active_directory_instance

    #     form_data = self.form_data
    #     form_data["rw_users"] = wustlkeys

    #     garbage_allocation = self.create_allocation(
    #         user=self.user, form_data=form_data
    #     )["allocation"]
    #     base_allocation = self.create_allocation(user=self.user, form_data=form_data)[
    #         "allocation"
    #     ]
    #     acl_allocation = AclAllocations.get_access_allocation(
    #         storage_allocation=base_allocation, resource_name="rw"
    #     )

    #     addUsersToADGroup(wustlkeys, acl_allocation, [])
    #     allocation_users = list(
    #         map(
    #             lambda allocation_user: allocation_user.user.username,
    #             AllocationUser.objects.filter(allocation=acl_allocation),
    #         )
    #     )
    #     self.assertListEqual(allocation_users, good_keys)

    #     garbage_acl_allocation = AclAllocations.get_access_allocation(
    #         storage_allocation=garbage_allocation, resource_name="rw"
    #     )
    #     garbage_allocation_users = list(
    #         map(
    #             lambda allocation_user: allocation_user.user.username,
    #             AllocationUser.objects.filter(allocation=garbage_acl_allocation),
    #         )
    #     )
    #     self.assertListEqual(garbage_allocation_users, wustlkeys)

    @patch("coldfront.plugins.qumulo.tasks.send_email_template")
    def test_sends_notifications_on_bad_users(
        self,
        mock_send_email_template: MagicMock,
        mock_active_directory_api: MagicMock,
        mock_allocation_view_AD: MagicMock,
        mock_allocation_view_async_task,
        mock_async_task,
    ):
        wustlkeys = ["foo", "bar"]
        self.form_data["rw_users"] = wustlkeys

        allocation = self.create_allocation(user=self.user, form_data=self.form_data)[
            "allocation"
        ]
        acl_allocation = AclAllocations.get_access_allocation(
            storage_allocation=allocation, resource_name="rw"
        )

        addUsersToADGroup([], acl_allocation, wustlkeys)

        mock_send_email_template.assert_called_once()

    def __get_user_mock(self, username: str, good_users: bool):
        if username in good_users:
            return None
        else:
            raise ValueError("Invalid wustlkey")

    def test_does_not_add_bad_users_to_group(
        self,
        mock_active_directory_api: MagicMock,
        mock_async_task: MagicMock,
        mock_allocation_view_AD: MagicMock,
        mock_allocation_view_async_task,
    ):
        active_directory_instance = MagicMock()
        active_directory_instance.get_user.side_effect = ValueError("Invalid wustlkey")
        mock_active_directory_api.return_value = active_directory_instance

        wustlkeys = ["foo"]
        self.form_data["rw_users"] = wustlkeys

        allocation = self.create_allocation(user=self.user, form_data=self.form_data)[
            "allocation"
        ]
        acl_allocation = AclAllocations.get_access_allocation(
            storage_allocation=allocation, resource_name="rw"
        )

        addUsersToADGroup(wustlkeys, acl_allocation)

        active_directory_instance.add_user_to_ad_group.assert_not_called()

    # def test_ads_good_users_to_allocation(
    #     self,
    #     mock_active_directory_api: MagicMock,
    #     mock_async_task: MagicMock,
    #     mock_allocation_view_AD: MagicMock,
    #     mock_allocation_view_async_task,
    # ):
    #     mock_async_task.side_effect = lambda *args: args[0](*args[1])

    #     wustlkeys = ["foo", "bar", "baz", "bah"]
    #     good_keys = wustlkeys[0:2]

    #     active_directory_instance = MagicMock()
    #     active_directory_instance.get_user.side_effect = (
    #         lambda username: self.__get_user_mock(username, good_keys)
    #     )
    #     mock_active_directory_api.return_value = active_directory_instance

    #     form_data = self.form_data
    #     form_data["rw_users"] = wustlkeys

    #     base_allocation = self.create_allocation(user=self.user, form_data=form_data)[
    #         "allocation"
    #     ]
    #     acl_allocation = AclAllocations.get_access_allocation(
    #         storage_allocation=base_allocation, resource_name="rw"
    #     )

    #     addUsersToADGroup(wustlkeys, acl_allocation, [])
    #     allocation_users = list(
    #         map(
    #             lambda allocation_user: allocation_user.user.username,
    #             AllocationUser.objects.filter(allocation=acl_allocation),
    #         )
    #     )
    #     self.assertListEqual(allocation_users, good_keys)


@patch("coldfront.plugins.qumulo.tasks.QumuloAPI")
class TestResetAcl(TestCase):
    def setUp(self) -> None:
        self.form_data = {
            "storage_filesystem_path": "/storage2/fs1/test_allocation",
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

        build_data = build_models()
        self.project = build_data["project"]
        self.user = build_data["user"]
        self.root_allocation = create_allocation(
            project=self.project, user=self.user, form_data=self.form_data
        )
        self._mockDirectoryExpectedValues()
        return super().setUp()

    def tearDown(self) -> None:
        return super().tearDown()

    def _createSubAllocation(self):
        sub_form_data = {
            "storage_filesystem_path": "/this/path/should/filter",
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
        return create_allocation(
            project=self.project,
            user=self.user,
            form_data=sub_form_data,
            parent=self.root_allocation,
        )

    def _mockDirectoryExpectedValues(self):
        self.mock_directory_expected_values = {}
        contents = enumerate_directory_contents("/fake/path")
        self.mock_directory_expected_values["total_entries"] = len(contents)
        expected_filter_count = 0
        for entry in contents:
            if not entry["path"].startswith("/this/path/should/filter"):
                expected_filter_count += 1
        self.mock_directory_expected_values["filtered_entries_count"] = (
            expected_filter_count
        )

    def test_reset_acl_on_sub_allocation_has_no_exclude_paths(
        self, qumulo_api_mock: MagicMock
    ):
        sub_allocation = self._createSubAllocation()
        reset = ResetAcl(sub_allocation)
        self.assertEqual(0, len(reset.reset_exclude_paths))

    def test_root_sub_allocation_reset_acl_exclude_path(
        self, qumulo_api_mock: MagicMock
    ):
        sub_allocation = self._createSubAllocation()
        reset = ResetAcl(self.root_allocation)
        self.assertEqual(1, len(reset.reset_exclude_paths))
        self.assertEqual(
            sub_allocation.get_attribute("storage_filesystem_path"),
            reset.reset_exclude_paths[0],
        )

    def test_reset_acl_directory_contents_filter(self, qumulo_api_mock: MagicMock):
        sub_allocation = self._createSubAllocation()
        reset = ResetAcl(self.root_allocation)
        reset.qumulo_api = MagicMock()
        reset.qumulo_api.rc.fs.enumerate_entire_directory.return_value = (
            enumerate_directory_contents("/pff")
        )
        contents = reset._get_directory_contents("/this/should/get/ignored")
        self.assertEqual(
            self.mock_directory_expected_values["filtered_entries_count"], len(contents)
        )
