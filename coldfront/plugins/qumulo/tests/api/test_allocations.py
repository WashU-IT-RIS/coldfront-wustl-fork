from django.test import TestCase
from django.http import HttpRequest

from unittest.mock import patch

from coldfront.plugins.qumulo.api.allocations import Allocations
from coldfront.plugins.qumulo.services.allocation_service import AllocationService

from coldfront.plugins.qumulo.tests.utils.mock_data import (
    build_models,
    default_form_data,
)

import json


@patch("coldfront.plugins.qumulo.services.allocation_service.async_task")
@patch("coldfront.plugins.qumulo.services.allocation_service.ActiveDirectoryAPI")
class TestAllocationsGet(TestCase):
    def setUp(self) -> None:
        build_data = build_models()

        self.user = build_data["user"]
        self.project = build_data["project"]

        return super().setUp()

    def test_get_returns_all_allocations(self, _, __) -> None:
        num_allocations = 3
        for i in range(num_allocations):
            form_data = default_form_data.copy()
            form_data["project_pk"] = self.project.pk
            form_data["storage_filesystem_path"] = f"test_path_{i}"

            AllocationService.create_new_allocation(form_data, self.user)

        allocations = Allocations()

        request = HttpRequest()
        request.method = "GET"
        response = allocations.get(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)), num_allocations)
