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
)
from coldfront.plugins.qumulo.tasks import ingest_quotas_with_daily_usage
from coldfront.plugins.qumulo.tests.utils.mock_data import (
    build_models,
    create_allocation,
)

from coldfront.plugins.qumulo.utils.eib_billing import EIBBilling

STORAGE2_PATH = os.environ.get("STORAGE2_PATH")


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
        (5, "consumption"),
        (15, "consumption"),
        (100, "consumption"),
        (5, "subscription"),
        (100, "subscription"),
        (500, "subscription"),
        (500, "subscription_500tb"),
        (500, "condo"),
    ]
    return allocation_attributes


def mock_get_names_quotas_usages():
    names_quotas_usages = [
        ("5tb-consumption", "5000000000000", "5000000000000"),
        ("15tb-consumption", "15000000000000", "10995116277760"),
        ("100tb-consumption", "100000000000000", "10995116277760"),
        ("5tb-subscription", "5000000000000", "1"),
        ("100tb-subscription", "100000000000000", "20"),
        ("500tb-subscription", "500000000000000", "200000000000000"),
        ("500tb-subscription_500tb", "500000000000000", "2"),
        ("500tb-condo", "500000000000000", "2"),
    ]
    return names_quotas_usages


def mock_get_quotas() -> str:
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


def mock_get_quota() -> str:
    name = "15tb-consumption"
    quota = "15000000000000"
    usage = "10995116277760"
    usage_in_json = [
        {
            "id": "101",
            "path": f"{STORAGE2_PATH}/{name}/",
            "limit": f"{quota}",
            "capacity_usage": f"{usage}",
        }
    ]

    return {
        "quotas": usage_in_json,
    }


class TestEIBBilling(TestCase):
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
        eib_billing = EIBBilling()
        header = eib_billing.get_report_header()
        self.assertTrue(re.search("^Submit Internal Service Delivery(,){27}", header))
        self.assertEqual(
            hashlib.md5(header.encode("utf-8")).hexdigest(),
            "250225b6615daaa68b067ceef5abaf51",
        )

    def test_query_return_sql_statement(self):
        eib_billing = EIBBilling()
        self.assertTrue(
            re.search("^\s*SELECT\s*", eib_billing.get_monthly_billing_query_template())
        )

    @patch("coldfront.plugins.qumulo.tasks.QumuloAPI")
    def test_create_an_allocation_ingest_usage_and_generate_billing_report(
        self, qumulo_api_mock: MagicMock
    ) -> None:
        qumulo_api = MagicMock()
        qumulo_api.get_all_quotas_with_usage.return_value = mock_get_quota()
        qumulo_api_mock.return_value = qumulo_api

        create_allocation(
            project=self.project,
            user=self.user,
            form_data=construct_allocation_form_data(15, "consumption"),
        )

        # Update the status of the created allocations from Pending to Active
        for allocation in Allocation.objects.filter(
            resources__name="Storage2",
            status__name__in=[
                "Pending",
            ],
        ):
            allocation.status = AllocationStatusChoice.objects.get(name="Active")
            allocation.save()

        # Confirm creating 1 Storage2 allocation
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT count(*)
                FROM allocation_allocation a
                JOIN allocation_allocation_resources ar
                    ON ar.allocation_id=a.id
                JOIN resource_resource r
                    ON r.id=ar.resource_id
                WHERE r.name='Storage2';
            """
            )
            rows = cursor.fetchall()

        self.assertEqual(1, rows[0][0])

        storage2_allocations = Allocation.objects.filter(resources__name="Storage2")
        self.assertEqual(1, len(storage2_allocations))

        # Exam the allocation attributes that have initial usage as 0.0
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT aa.allocation_id,
                    storage_filesystem_path,
                    aa.value quota_tb,
                    aau.value usage,
                    ROUND(CAST(aau.value AS NUMERIC)/1024/1024/1024/1024, 2) usage_tb
                FROM allocation_allocationattribute aa
                LEFT JOIN allocation_allocationattributetype aat
                    ON aa.allocation_attribute_type_id = aat.id
                LEFT JOIN allocation_allocationattributeusage aau
                    ON aa.id=aau.allocation_attribute_id
                LEFT JOIN (
                    SELECT aa.allocation_id, aa.value storage_filesystem_path
                        FROM allocation_allocationattribute aa
                        JOIN allocation_allocationattributetype aat
                           ON aa.allocation_attribute_type_id=aat.id
                        WHERE aat.name='storage_filesystem_path'
                    ) AS storage_filesystem_path
                    ON aa.allocation_id=storage_filesystem_path.allocation_id
                WHERE aat.has_usage IS TRUE;
            """
            )
            rows = cursor.fetchall()

        for row in rows:
            # Confirm the initial usage is 0
            self.assertEqual(float(row[3]) - 0, 0)

        ingest_quotas_with_daily_usage()

        # Exam the billing usage of the allocation from the history table
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT aa.allocation_id id,
                    storage_filesystem_path path,
                    aa.value quota,
                    aau.value now_usage,
                    ROUND(CAST(aau.value AS NUMERIC) /1024/1024/1024/1024, 2) now_usage_tb,
                    ROUND(CAST(storage_usage_of_the_day.storage_usage AS NUMERIC) /1024/1024/1024/1024, 2) history_usage_tb,
                    aa.created,
                    storage_usage_of_the_day.usage_timestamp history_timestamp
                FROM allocation_allocationattributeusage aau
                JOIN allocation_allocationattribute aa
                    ON aa.id = aau.allocation_attribute_id
                JOIN (
                    SELECT haau.allocation_attribute_id, haau.value storage_usage, haau.modified usage_timestamp
                    FROM allocation_historicalallocationattributeusage haau
                    JOIN (
                        SELECT allocation_attribute_id aa_id, MAX(modified) usage_timestamp
                        FROM allocation_historicalallocationattributeusage
                        GROUP BY aa_id, DATE(modified)
                    ) AS aa_id_usage_timestamp
                        ON haau.allocation_attribute_id = aa_id_usage_timestamp.aa_id
                            AND haau.modified = aa_id_usage_timestamp.usage_timestamp
                ) AS storage_usage_of_the_day
                    ON aau.allocation_attribute_id = storage_usage_of_the_day.allocation_attribute_id
                JOIN allocation_allocationattributetype aat
                    ON aat.id = aa.allocation_attribute_type_id
                JOIN (
                    SELECT aa.allocation_id, aa.value storage_filesystem_path
                        FROM allocation_allocationattribute aa
                        JOIN allocation_allocationattributetype aat
                           ON aa.allocation_attribute_type_id = aat.id
                        WHERE aat.name = 'storage_filesystem_path'
                    ) AS storage_filesystem_path
                    ON aa.allocation_id = storage_filesystem_path.allocation_id
                ORDER BY id DESC, history_timestamp DESC;
            """
            )
            rows = cursor.fetchall()

        for row in rows:
            # Confirm the new usage is not 0
            print(row)
            self.assertNotEqual(float(row[3]) - 0, 0)

        # Confirm the status of the allocation is Active
        allocations = Allocation.objects.filter(resources__name="Storage2").exclude(
            status__name__in=[
                "Active",
            ]
        )
        self.assertEqual(len(list(allocations)), 0)

        eib_billing = EIBBilling(datetime.now(timezone.utc).strftime("%Y-%m-%d"))
        eib_billing.generate_monthly_billing_report()

        filename = eib_billing.get_filename()
        self.assertFalse(re.search("RIS-%s-storage2-active-billing.csv", filename))
        self.assertTrue(
            re.search("RIS-[A-Za-z]+-storage2-active-billing.csv", filename)
        )
        self.assertTrue(os.path.exists(filename))
        os.system(f"ls -l {filename}")

        with open(filename) as csvreport:
            data = list(csv.reader(csvreport))

        # Confirm the billing amount for 5 unit of Consumption cost model is $65
        # hardcoded
        billing_amount = float(data[len(data) - 1][19])
        self.assertEqual(billing_amount - 65.0, 0)

        os.remove(filename)

    @patch("coldfront.plugins.qumulo.tasks.QumuloAPI")
    def test_create_allocations_ingest_usages_generate_billing_report(
        self, qumulo_api_mock: MagicMock
    ) -> None:
        qumulo_api = MagicMock()
        qumulo_api.get_all_quotas_with_usage.return_value = mock_get_quotas()
        qumulo_api_mock.return_value = qumulo_api

        quota_service_rate_categories = mock_get_quota_service_rate_categories()

        for quota, service_rate_category in quota_service_rate_categories:
            create_allocation(
                project=self.project,
                user=self.user,
                form_data=construct_allocation_form_data(quota, service_rate_category),
            )

        # Update the status of the created allocations from Pending to Active
        for allocation in Allocation.objects.filter(
            resources__name="Storage2",
            status__name__in=[
                "Pending",
            ],
        ):
            allocation.status = AllocationStatusChoice.objects.get(name="Active")
            allocation.save()

        storage2_allocations = Allocation.objects.filter(
            resources__name="Storage2", status__name__in=["Active"]
        )
        self.assertEqual(len(storage2_allocations), len(quota_service_rate_categories))

        ingest_quotas_with_daily_usage()
        eib_billing = EIBBilling(datetime.now(timezone.utc).strftime("%Y-%m-%d"))
        eib_billing.generate_monthly_billing_report()

        filename = eib_billing.get_filename()
        with open(filename) as csvreport:
            data = list(csv.reader(csvreport))

        header = eib_billing.get_report_header()
        num_lines_header = len(header.splitlines())
        print("Numer of lines of the report header: %s" % num_lines_header)
        self.assertEqual(num_lines_header, 5)

        row = 1
        for index in range(num_lines_header, len(data)):
            row_num = data[index][1]
            self.assertEqual(str(row), row_num)
            billing_amount = data[index][19].replace('"', "")
            fileset_memo = data[index][22].replace('"', "")

            # Confirm the billing amounts of each test cases
            # hardcoded
            if fileset_memo == "5tb-consumption":
                self.assertFalse(True)
            elif fileset_memo == "15tb-consumption":
                self.assertEqual(float(billing_amount) - 65.0, 0)
            elif fileset_memo == "100tb-consumption":
                self.assertEqual(float(billing_amount) - 65.0, 0)
            elif fileset_memo == "5tb-subscription":
                self.assertEqual(float(billing_amount) - 634.0, 0)
            elif fileset_memo == "100tb-subscription":
                self.assertEqual(float(billing_amount) - 634.0, 0)
            elif fileset_memo == "500tb-subscription":
                self.assertEqual(float(billing_amount) - 3170.0, 0)
            elif fileset_memo == "500tb-subscription_500tb":
                self.assertEqual(float(billing_amount) - 2643.0, 0)
            elif fileset_memo == "500tb-condo":
                self.assertEqual(float(billing_amount) - 529.0, 0)
            else:
                print(fileset_memo, billing_amount)
                self.assertFalse(True)
            row += 1

        os.remove(filename)
