import datetime
import pprint
from random import random

from typing import Tuple

from django.test import TestCase
from django.http import HttpRequest

from coldfront.core.allocation.models import Allocation, AllocationAttribute, AllocationAttributeUsage
from coldfront.core.test_helpers.factories import AllocationAttributeUsageFactory

from coldfront.plugins.qumulo.api.usage import Usage
from coldfront.plugins.qumulo.tests import fixtures_usages
from coldfront.plugins.qumulo.tests.fixtures import (create_metadata_for_testing, create_ris_project_and_allocations_storage3)

import json

def _create_allocation_with_usage(quota_tib: int, usage_gib: float) -> Tuple[Allocation, AllocationAttributeUsage]:
  _, allocations = create_ris_project_and_allocations_storage3(
        storage_filesystem_path="/storage3/fs1/testuser",
    )
  storage_allocation = allocations["storage_allocation"]
  storage_quota = AllocationAttribute.objects.get(allocation=storage_allocation, allocation_attribute_type__name="storage_quota")
  
  storage_quota.value = quota_tib
  storage_quota.save()
  
  quota_usage:AllocationAttributeUsage = AllocationAttributeUsageFactory(
      allocation_attribute=allocations[
          "storage_allocation"
      ].allocationattribute_set.get(allocation_attribute_type__name="storage_quota"),
      value=usage_gib * 2**30,
  )
  
  return (storage_allocation, quota_usage)

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
    
    (storage_allocation,_) = _create_allocation_with_usage(expected_quota_tib, expected_usage)
    
    self.request.GET.update({'allocation_id': storage_allocation.pk})
    response = self.usage.get(self.request)
    content = json.loads(response.content)
    
    self.assertEqual(response.status_code, 200)
    self.assertEqual(content['allocation_id'], storage_allocation.pk)
    self.assertEqual(content['quota'], expected_quota_tib * 1024)
    self.assertEqual(content['usage'][0]['usage'], expected_usage)
    
  def test_returns_usage_for_specific_date(self) -> None:
    expected_quota_tib = 5
    current_usage_gib = 3.25 * 1024
    expected_usage_gib = 2.6 * 1024
    date = '2025-01-01'
    
    (storage_allocation, usage_object) = _create_allocation_with_usage(expected_quota_tib, current_usage_gib)
    
    usage_object.value = expected_usage_gib * 2**30
    usage_object._history_date = datetime.datetime.fromisoformat(date)
    usage_object.save()
  
    self.request.GET.update({'allocation_id': storage_allocation.pk, 'date': date})
    response = self.usage.get(self.request)
    content = json.loads(response.content)
    
    self.assertEqual(response.status_code, 200)
    self.assertEqual(content['allocation_id'], storage_allocation.pk)
    self.assertEqual(content['date'], date)
    self.assertEqual(content['quota'], expected_quota_tib * 1024)
    self.assertEqual(content['usage'][0]['usage'], expected_usage_gib)
    
  def test_returns_monthly_list_by_year(self) -> None:
    expected_quota_tib = 5
    current_usage_gib = 4.75 * 1024
    
    (storage_allocation, usage_object) = _create_allocation_with_usage(expected_quota_tib, current_usage_gib)
    
    usage_history = []
    today = datetime.date.today()
    
    for i in range(12):
      current_month = today.month
      new_month = current_month - i
      if new_month > 0:
        working_date = today.replace(day=1, month=new_month)
      else:
        new_month = current_month - i + 12
        working_date = today.replace(day=1, month=new_month, year=today.year-1)
      
      usage_tib = round(random() * expected_quota_tib, 12)
      
      usage_history.insert(0,{"usage": usage_tib * 2**10, "date": working_date.isoformat()})
      
      usage_object.value = usage_tib * 2**40
      usage_object._history_date = working_date
      usage_object.save()
      
    usage_history.append({"usage": current_usage_gib, "date": today.isoformat()})
        
    self.request.GET.update({'allocation_id': storage_allocation.pk})
    response = self.usage.get(self.request)
    content = json.loads(response.content)
    
    self.assertEqual(response.status_code, 200)
    self.assertEqual(content['allocation_id'], storage_allocation.pk)
    self.assertEqual(content['quota'], expected_quota_tib * 1024)
    self.assertIsInstance(content['usage'], list)
    self.assertListEqual(content['usage'], usage_history)