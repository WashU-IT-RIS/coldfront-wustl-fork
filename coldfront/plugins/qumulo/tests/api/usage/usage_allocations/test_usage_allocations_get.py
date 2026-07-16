from datetime import date, datetime, timedelta

from django.test import TestCase
from django.http import HttpRequest

from coldfront.core.test_helpers.factories import (
    UserFactory,
    AllocationAttributeFactory,
)

from coldfront.plugins.qumulo.api.usage.usage_allocations import UsageAllocations
from coldfront.plugins.qumulo.tests.fixtures import (
    create_metadata_for_testing, create_ris_project_and_allocations_storage3
)
from coldfront.plugins.qumulo.tests.api.usage.helpers import (
    create_allocation_with_usage,
    create_usage_history,
    get_history_span,
)

import json
from faker import Faker
from faker.providers import person
from pprint import pprint

fake = Faker()
fake.add_provider(person)



class TestUsageAllocationsGet(TestCase):
    def setUp(self) -> None:
        create_metadata_for_testing()

        # self.expected_quota_tib = 5
        # self.expected_usage = 3.25 * 1024

        # (storage_allocation, _) = create_allocation_with_usage(
        #     self.expected_quota_tib, self.expected_usage
        # )
        # self.storage_allocation_pk = storage_allocation.pk
        
        self.usage_allocations = UsageAllocations()

        self.request = HttpRequest()
        self.request.method = "GET"

        return super().setUp()
    
    def test_admin_gets_all_allocations(self):
        expected_allocation_count = 5
        user = UserFactory.create(is_superuser=True)
        
        for i in range(expected_allocation_count):
            end_path=fake.last_name()
            create_ris_project_and_allocations_storage3(f"/storage3/fs1/{end_path}")
        
        self.client.force_login(user)    
        response = self.client.get("/qumulo/api/usage/allocations")
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['allocations']), expected_allocation_count)