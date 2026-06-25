import datetime

from django.test import TestCase
from django.http import HttpRequest

from coldfront.core.allocation.models import AllocationAttribute, AllocationAttributeUsage
from coldfront.core.test_helpers.factories import AllocationAttributeUsageFactory

from coldfront.plugins.qumulo.api.usage import Usage
from coldfront.plugins.qumulo.tests import fixtures_usages
from coldfront.plugins.qumulo.tests.fixtures import (create_metadata_for_testing, create_ris_project_and_allocations_storage3)



import json

class TestUsageGet(TestCase):
  def setUp(self) -> None:
    create_metadata_for_testing()
    
    self.usage = Usage()
    
    self.request = HttpRequest()
    self.request.method = "GET"
    
    return super().setUp()
    
  def test_returns_200(self) -> None:
    response = self.usage.get(self.request)
    
    self.assertEqual(response.status_code, 200)
    
  def test_returns_latest_usage_for_specified_allocation(self) -> None:
    expected_quota_tib = 5
    expected_usage = 3.25 * 1024
    
    _, allocations = create_ris_project_and_allocations_storage3(
        storage_filesystem_path="/storage3/fs1/testuser",
    )
    storage_allocation = allocations["storage_allocation"]
    storage_quota = AllocationAttribute.objects.get(allocation=storage_allocation, allocation_attribute_type__name="storage_quota")
    
    storage_quota.value = expected_quota_tib
    storage_quota.save()
    
    AllocationAttributeUsageFactory(
        allocation_attribute=allocations[
            "storage_allocation"
        ].allocationattribute_set.get(allocation_attribute_type__name="storage_quota"),
        value=expected_usage * 2**30,
    )
    
    self.request.GET.update({'allocation_id': storage_allocation.pk})
    response = self.usage.get(self.request)
    content = json.loads(response.content)
    
    self.assertEqual(response.status_code, 200)
    self.assertEqual(content['allocation_id'], storage_allocation.pk)
    self.assertEqual(content['quota'], expected_quota_tib * 1024)
    self.assertEqual(content['usage'], expected_usage)
    
  def test_returns_usage_for_specific_date(self) -> None:
    expected_quota_tib = 5
    current_usage_gib = 3.25 * 1024
    expected_usage = 2.6 * 1024
    date = '2025-01-01'
    
    _, allocations = create_ris_project_and_allocations_storage3(
        storage_filesystem_path="/storage3/fs1/testuser",
    )
    storage_allocation = allocations["storage_allocation"]
    storage_quota = AllocationAttribute.objects.get(allocation=storage_allocation, allocation_attribute_type__name="storage_quota")
    
    storage_quota.value = expected_quota_tib
    storage_quota.save()
    
    usage_object: AllocationAttributeUsage = AllocationAttributeUsageFactory(
        allocation_attribute=allocations[
            "storage_allocation"
        ].allocationattribute_set.get(allocation_attribute_type__name="storage_quota"),
        value=current_usage_gib * 2**30,
    )
    
    usage_object.value = expected_usage * 2**30
    usage_object._history_date = datetime.datetime.fromisoformat(date)
    usage_object.save()
  
    self.request.GET.update({'allocation_id': storage_allocation.pk, 'date': date})
    response = self.usage.get(self.request)
    content = json.loads(response.content)
    
    self.assertEqual(response.status_code, 200)
    self.assertEqual(content['allocation_id'], storage_allocation.pk)
    self.assertEqual(content['date'], date)
    self.assertEqual(content['quota'], expected_quota_tib * 1024)
    self.assertEqual(content['usage'], expected_usage)