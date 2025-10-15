from django.test import TestCase

from unittest.mock import patch, MagicMock, ANY

from coldfront.plugins.qumulo.tests.utils.mock_data import (
    build_models,
    create_allocation,
    enumerate_directory_contents,
    default_form_data,
)
from coldfront.plugins.qumulo.tasks import (
    ResetAcl,
)


@patch("coldfront.plugins.qumulo.tasks.QumuloAPI")
class TestResetAcl(TestCase):
    def setUp(self) -> None:
        build_data = build_models()
        self.project = build_data["project"]
        self.user = build_data["user"]

        self.form_data = default_form_data.copy()
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
            "billing_exempt": "No",
            "department_number": "Time Travel Services",
            "billing_cycle": "monthly",
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
