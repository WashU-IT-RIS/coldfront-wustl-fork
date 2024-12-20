import os
import csv
import re
import hashlib
from datetime import datetime, timezone

from django.db import connection
from django.test import TestCase, Client
from unittest.mock import patch, MagicMock

from coldfront.core.allocation.models import (
    Allocation,
    AllocationStatusChoice,
    AllocationAttributeType,
    AllocationLinkage,
)
from coldfront.plugins.qumulo.tasks import ingest_quotas_with_daily_usage
from coldfront.plugins.qumulo.tests.utils.mock_data import (
    build_models,
    create_allocation,
)

from coldfront.plugins.qumulo.utils.prepaid_billing import PrepaidBilling

STORAGE2_PATH = os.environ.get("STORAGE2_PATH")

REPORT_COLUMNS = [
    "fields",
    "spreadsheet_key",
    "add_only",
    "auto_complete",
    "internal_service_delivery_id",
    "submit",
    "company",
    "internal_service_provider",
    "currency",
    "document_date",
    "memo",
    "row_id",
    "internal_service_delivery_line_id",
    "internal_service_delivery_line_number",
    "item_description",
    "spend_category",
    "quantity",
    "unit_of_measure",
    "unit_cost",
    "extended_amount",
    "requester",
    "delivery_date",
    "memo_filesets",
    "cost_center",
    "prepaid_expiration",
    "prepaid_time",
    "fund",
    "spacer_1",
    "spacer_2",
    "spacer_3",
    "usage",
    "rate",
    "unit",
]


def construct_allocation_form_data(quota_tb: int, service_rate_category: str):
    form_data = {
        "storage_name": f"{quota_tb}tb-{service_rate_category}",
        "storage_quota": str(quota_tb),
        "protocols": ["smb"],
        "storage_filesystem_path": f"{STORAGE2_PATH}/{quota_tb}tb-{service_rate_category}",
        "storage_export_path": f"{STORAGE2_PATH}/{quota_tb}tb-{service_rate_category}",
        "rw_users": ["test"],
        "ro_users": ["test1"],
        "storage_ticket": "ITSD-1234",
        "cost_center": "CC0000123",
        "department_number": "CH000123",
        "billing_cycle": "monthly",
        "service_rate": service_rate_category,
    }
    return form_data


def construct_suballocation_form_data(quota_tb: int, parent_allocation: Allocation):
    form_data = {
        "parent_allocation_name": parent_allocation.get_attribute("storage_name"),
        "storage_name": f"{quota_tb}tb-suballocation",
        "storage_quota": str(quota_tb),
        "protocols": ["smb"],
        "storage_filesystem_path": f"{parent_allocation.get_attribute('storage_filesystem_path')}/Active/{quota_tb}tb-suballocation",
        "storage_export_path": f"{parent_allocation.get_attribute('storage_export_path')}/Active/{quota_tb}tb-suballocation",
        "rw_users": ["test"],
        "ro_users": ["test1"],
        "storage_ticket": "ITSD-1234",
        "cost_center": parent_allocation.get_attribute("cost_center"),
        "department_number": parent_allocation.get_attribute("department_number"),
        "billing_cycle": parent_allocation.get_attribute("billing_cycle"),
        "service_rate": parent_allocation.get_attribute("service_rate"),
    }
    return form_data


def construct_usage_data_in_json(filesystem_path: str, quota: str, usage: str):
    quota_in_json = {
        "id": "100",
        "path": f"{filesystem_path}",
        "limit": f"{quota}",
        "capacity_usage": f"{usage}",
    }
    return quota_in_json


def mock_get_quota_service_rate_categories():
    allocation_attributes = [
        (5, "subscription"),
        (100, "subscription"),
        (500, "subscription"),
        (500, "subscription_500tb"),
    ]
    return allocation_attributes


def mock_get_names_quotas_usages():
    names_quotas_usages = [
        ("5tb-subscription", "5000000000000", "1"),
        ("100tb-subscription", "100000000000000", "20"),
        ("500tb-subscription", "500000000000000", "200000000000000"),
        ("500tb-subscription_500tb", "500000000000000", "2"),
    ]
    return names_quotas_usages


def mock_get_multiple_quotas() -> str:
    usages_in_json = []
    json_id = 100
    for name, quota, usage in mock_get_names_quotas_usages():
        usage_in_json = construct_usage_data_in_json(
            f"{STORAGE2_PATH}/{name}", quota, usage
        )
        usage_in_json[id] = json_id
        usages_in_json.append(usage_in_json)
        json_id += 1

    return {
        "quotas": usages_in_json,
    }


class TestPrepaidBilling(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        build_data = build_models()

        self.project = build_data["project"]
        self.user = build_data["user"]

        self.storage_filesystem_path_attribute_type = (
            AllocationAttributeType.objects.get(name="storage_filesystem_path")
        )
        self.storage_quota_attribute_type = AllocationAttributeType.objects.get(
            name="storage_quota"
        )
        return super().setUp()

    def test_header_return_csv(self):
        prepaid_billing = PrepaidBilling()
        header = prepaid_billing.get_report_header()
        self.assertTrue(re.search("^Submit Internal Service Delivery(,){27}", header))
        self.assertEqual(
            hashlib.md5(header.encode("utf-8")).hexdigest(),
            "250225b6615daaa68b067ceef5abaf51",
        )

    def test_query_return_sql_statement(self):
        prepaid_billing = PrepaidBilling()
        self.assertTrue(
            re.search(
                "^\s*SELECT\s*", prepaid_billing.get_prepaid_billing_query_template()
            )
        )
