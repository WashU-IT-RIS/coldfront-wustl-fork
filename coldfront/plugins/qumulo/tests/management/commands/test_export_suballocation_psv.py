from django.test import TestCase,Client
from django.contrib.auth.models import User
from django.core.management import call_command

from unittest.mock import patch, MagicMock

from coldfront.core.project.models import Project
from coldfront.plugins.qumulo.services.allocation_service import AllocationService
from coldfront.plugins.qumulo.tests.utils.mock_data import (
    build_models,default_form_data
)

from io import StringIO

@patch("coldfront.plugins.qumulo.services.allocation_service.async_task")
@patch("coldfront.plugins.qumulo.services.allocation_service.ActiveDirectoryAPI")
@patch("coldfront.plugins.qumulo.tasks.ActiveDirectoryAPI")
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

      return super().setUp()
    
  def call_command(self, *args, **kwargs):
        out = StringIO()
        err = StringIO()
        call_command(
            # "my_custom_command",
            *args,
            stdout=out,
            stderr=err,
            **kwargs,
        )
        return out.getvalue(), err.getvalue()
    
  def test_single_parent_prints_expected_output(self,mock_active_directory_api: MagicMock,mock_allocation_view_AD: MagicMock,mock_allocation_view_async_task: MagicMock):
    filesystem_path = "/storage3/fs1/foo"
    self.form_data["storage_filesystem_path"] = filesystem_path
    self.form_data["storage_type"] = "Storage3"
    
    self.create_allocation(user=self.user, form_data=self.form_data)[
        "allocation"
    ]
    
    out, err = self.call_command("export_suballocation_psv", "--allocations", filesystem_path)
    
    expected_output = filesystem_path + "|{}\n"
    self.assertEqual(expected_output,out)
    