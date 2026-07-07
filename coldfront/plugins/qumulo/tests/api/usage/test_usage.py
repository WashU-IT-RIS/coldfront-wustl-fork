from datetime import date, datetime, timedelta
from random import random

from typing import Tuple

from django.test import TestCase
from django.http import HttpRequest

from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttribute,
    AllocationAttributeUsage,
)
from coldfront.core.test_helpers.factories import AllocationAttributeUsageFactory

from coldfront.plugins.qumulo.api.usage import Usage
from coldfront.plugins.qumulo.tests.fixtures import (
    create_metadata_for_testing,
    create_ris_project_and_allocations_storage3,
)
from coldfront.plugins.qumulo.tests.api.usage.helpers import (
    create_allocation_with_usage,
)

import json

from pprint import pprint


class TestUsage(TestCase):
    def setUp(self):
        create_metadata_for_testing()

        return super().setUp()

    def test_restricts_anonymous_users(self):
        expected_quota_tib = 5
        expected_usage = 3.25 * 1024

        (storage_allocation, _) = create_allocation_with_usage(
            expected_quota_tib, expected_usage
        )

        response = self.client.get(
            "/qumulo/api/usage", {"allocation_id": storage_allocation.pk}
        )

        self.assertEqual(response.status_code, 302)
