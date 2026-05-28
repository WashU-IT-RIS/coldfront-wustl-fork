import json
import os
from unittest import skip

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.management import call_command

from unittest.mock import patch, MagicMock

from factory import faker

from coldfront.core.allocation.models import Allocation
from coldfront.core.project.models import Project
from coldfront.core.test_helpers.factories import (
    AllocationAttributeFactory,
    AllocationAttributeTypeFactory,
)
from coldfront.core.test_helpers.factories import AllocationAttributeTypeFactory
from coldfront.plugins.qumulo.services.allocation_service import AllocationService
from coldfront.plugins.qumulo.tests.fixtures import (
    create_allocation_attribute,
    create_allocation_with_allocation_attributes,
    create_metadata_for_testing,
    create_sub_allocation,
)
from coldfront.plugins.qumulo.tests.helper_classes.factories import Storage3Factory
from coldfront.plugins.qumulo.tests.utils.mock_data import (
    build_models,
    default_form_data,
    mock_qumulo_info,
)

from io import StringIO


class TestExportSuballocationPsv(TestCase):
    def setUp(self) -> None:

        self.client = Client()

        build_data = build_models()

        self.project: Project = build_data["project"]
        self.user: User = build_data["user"]

        self.form_data = default_form_data.copy()
        self.form_data["project_pk"] = self.project.id

        self.client.force_login(self.user)

        self.create_allocation = AllocationService.create_new_allocation

        self.storage_filesystem_path_type = AllocationAttributeTypeFactory(
            name="storage_filesystem_path"
        )

        return super().setUp()

    def call_command(self, *args, **kwargs):
        out = StringIO()
        err = StringIO()
        call_command(
            *args,
            stdout=out,
            stderr=err,
            **kwargs,
        )
        return out.getvalue(), err.getvalue()

    def test_single_parent_prints_expected_output(self):
        filesystem_path = f"/storage3/fs1//foo"
        create_allocation_with_allocation_attributes(
            storage_factory=Storage3Factory, storage_filesystem_path=filesystem_path
        )

        out, _ = self.call_command(
            "export_suballocation_psv", "--allocations", filesystem_path
        )

        expected_output = f"{filesystem_path}|{{}}\n"

        self.assertEqual(expected_output, out)

    def test_single_parent_with_child(self):
        filesystem_path = f"/storage3/fs1/foo"
        suballocation_subpath = f"{filesystem_path}/bah"
        parent_allocation = create_allocation_with_allocation_attributes(
            storage_factory=Storage3Factory, storage_filesystem_path=filesystem_path
        )["allocations"]["storage_allocation"]
        sub_allocation = create_sub_allocation(parent=parent_allocation)
        create_allocation_attribute(
            sub_allocation, "storage_filesystem_path", suballocation_subpath
        )

        out, _ = self.call_command(
            "export_suballocation_psv", "--allocations", filesystem_path
        )

        expected_output = f"{filesystem_path}|{{{suballocation_subpath}}}\n"
        self.assertEqual(expected_output, out)

    def test_multiple_basic_allocations(self):

        allocations: list[Allocation] = Storage3Factory.create_batch(2)
        paths: list[str] = []
        for allocation in allocations:
            allocation_attribute = create_allocation_attribute(
                allocation, "storage_filesystem_path", faker.Faker("file_path", depth=2)
            )
            paths.append(allocation_attribute.value)

        out, _ = self.call_command(
            "export_suballocation_psv",
            "--allocations",
            *paths,
        )
        expected_output = "".join(f"{path}|{{}}\n" for path in paths)

        self.assertEqual(expected_output, out)

    @patch("coldfront.plugins.qumulo.services.allocation_service.async_task")
    @patch("coldfront.plugins.qumulo.services.allocation_service.ActiveDirectoryAPI")
    @patch("coldfront.plugins.qumulo.tasks.ActiveDirectoryAPI")
    @patch.dict(os.environ, {"QUMULO_INFO": json.dumps(mock_qumulo_info)})
    def test_multiple_allocations(
        self,
        mock_active_directory_api: MagicMock,
        mock_allocation_view_AD: MagicMock,
        mock_allocation_view_async_task: MagicMock,
    ):
        self.form_data["storage_type"] = "Storage3"
        filesystem_path = (
            f"{mock_qumulo_info[self.form_data['storage_type']]['path']}/foo"
        )
        self.form_data["storage_filesystem_path"] = filesystem_path

        self.create_allocation(user=self.user, form_data=self.form_data)

        allocation2_form_data = default_form_data.copy()
        allocation2_form_data["project_pk"] = self.project.id
        allocation2_filesystem_path = (
            f"{mock_qumulo_info[allocation2_form_data['storage_type']]['path']}/bar"
        )
        allocation2_form_data["storage_filesystem_path"] = allocation2_filesystem_path

        allocation2 = self.create_allocation(
            user=self.user, form_data=allocation2_form_data
        )["allocation"]

        suballocation_form_data = default_form_data.copy()
        suballocation_subpath = "bah"
        suballocation_form_data["project_pk"] = self.project.id
        suballocation_form_data["storage_filesystem_path"] = suballocation_subpath

        self.create_allocation(
            user=self.user,
            form_data=suballocation_form_data,
            parent_allocation=allocation2,
        )

        out, err = self.call_command(
            "export_suballocation_psv",
            "--allocations",
            filesystem_path,
            allocation2_filesystem_path,
        )

        expected_output = (
            filesystem_path
            + "|{}\n"
            + allocation2_filesystem_path
            + "|{"
            + suballocation_subpath
            + "}\n"
        )

        self.assertEqual(expected_output, out)
