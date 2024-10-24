import os
import re
import hashlib
from datetime import datetime

from django.db import connection
from django.test import TestCase, Client
from unittest.mock import patch, MagicMock

from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttribute,
    AllocationAttributeType,
)
from coldfront.plugins.qumulo.forms import AllocationForm
from coldfront.plugins.qumulo.tasks import ingest_quotas_with_daily_usage
from coldfront.plugins.qumulo.tests.utils.mock_data import (
    build_models,
    create_allocation,
)

from coldfront.plugins.qumulo.utils.eib_billing import (
    get_report_header,
    get_monthly_billing_query_template,
    get_filename,
    generate_monthly_billing_report,
)

def set_allocation_form_data_with_5TB_consumption():
    form_data = {
        "storage_name": '5tb-consumption',
        "storage_quota": '5',
        "protocols": ["smb"],
        "storage_filesystem_path": '/storage2/fs1/5tb-consumption',
        "storage_export_path": '/storage2/fs1/5tb-consumption',
        "rw_users": ['test'],
        "ro_users": ['test1'],
        "storage_ticket": 'ITSD-1234',
        "cost_center": 'CC0000123',
        "department_number": 'CH000123',
        "service_rate": 'consumption',
    }
    return form_data

def set_allocation_form_data_with_15TB_consumption():
    form_data = {
        "storage_name": '15tb-consumption',
        "storage_quota": '15',
        "protocols": ["smb"],
        "storage_filesystem_path": '/storage2/fs1/15tb-consumption',
        "storage_export_path": '/storage2/fs1/15tb-consumption',
        "rw_users": ['test'],
        "ro_users": ['test1'],
        "storage_ticket": 'ITSD-1234',
        "cost_center": 'CC0000123',
        "department_number": 'CH000123',
        "service_rate": 'consumption',
    }
    return form_data

def set_allocation_form_data_with_100TB_consumption():
    form_data = {
        "storage_name": '100tb-consumption',
        "storage_quota": '100',
        "protocols": ["smb"],
        "storage_filesystem_path": '/storage2/fs1/100tb-consumption',
        "storage_export_path": '/storage2/fs1/100tb-consumption',
        "rw_users": ['test'],
        "ro_users": ['test1'],
        "storage_ticket": 'ITSD-1234',
        "cost_center": 'CC0000123',
        "department_number": 'CH000123',
        "service_rate": 'consumption',
    }
    return form_data

def set_allocation_form_data_with_5TB_subscription():
    form_data = {
        "storage_name": '5tb-subscription',
        "storage_quota": '5',
        "protocols": ["smb"],
        "storage_filesystem_path": '/storage2/fs1/5tb-subscription',
        "storage_export_path": '/storage2/fs1/5tb-subscription',
        "rw_users": ['test'],
        "ro_users": ['test1'],
        "storage_ticket": 'ITSD-1234',
        "cost_center": 'CC0000123',
        "department_number": 'CH000123',
        "service_rate": 'subscription',
    }
    return form_data

def set_allocation_form_data_with_100TB_subscription():
    form_data = {
        "storage_name": '100tb-subscription',
        "storage_quota": '100',
        "protocols": ["smb"],
        "storage_filesystem_path": '/storage2/fs1/100tb-subscription',
        "storage_export_path": '/storage2/fs1/100tb-subscription',
        "rw_users": ['test'],
        "ro_users": ['test1'],
        "storage_ticket": 'ITSD-1234',
        "cost_center": 'CC0000123',
        "department_number": 'CH000123',
        "service_rate": 'subscription',
    }
    return form_data

def set_allocation_form_data_with_500TB_subscription():
    form_data = {
        "storage_name": '500tb-subscription',
        "storage_quota": '500',
        "protocols": ["smb"],
        "storage_filesystem_path": '/storage2/fs1/500tb-subscription',
        "storage_export_path": '/storage2/fs1/500tb-subscription',
        "rw_users": ['test'],
        "ro_users": ['test1'],
        "storage_ticket": 'ITSD-1234',
        "cost_center": 'CC0000123',
        "department_number": 'CH000123',
        "service_rate": 'subscription',
    }
    return form_data

def set_allocation_form_data_with_1000TB_subscription():
    form_data = {
        "storage_name": '1000tb-subscription',
        "storage_quota": '1000',
        "protocols": ["smb"],
        "storage_filesystem_path": '/storage2/fs1/1000tb-subscription',
        "storage_export_path": '/storage2/fs1/1000tb-subscription',
        "rw_users": ['test'],
        "ro_users": ['test1'],
        "storage_ticket": 'ITSD-1234',
        "cost_center": 'CC0000123',
        "department_number": 'CH000123',
        "service_rate": 'subscription',
    }
    return form_data

def set_allocation_form_data_with_500TB_condo():
    form_data = {
        "storage_name": '500tb-condo',
        "storage_quota": '500',
        "protocols": ["smb"],
        "storage_filesystem_path": '/storage2/fs1/500tb-condo',
        "storage_export_path": '/storage2/fs1/500tb-condo',
        "rw_users": ['test'],
        "ro_users": ['test1'],
        "storage_ticket": 'ITSD-1234',
        "cost_center": 'CC0000123',
        "department_number": 'CH000123',
        "service_rate": 'condo',
    }
    return form_data

def mock_get_quotas_1() -> str:
    return{
        "quotas": [
            {
                "id": "100",
                "path": "/storage2/fs1/5tb-consumption",
                "limit": "5000000000000",
                "capacity_usage": "100",                
            },
        ]
    }

def mock_get_quotas_2() -> str:
    return{
        "quotas": [
            {
                "id": "100",
                "path": "/storage2/fs1/5tb-consumption",
                "limit": "5000000000000",
                "capacity_usage": "5000000000000",                
            },
            {
                "id": "101",
                "path": "/storage2/fs1/15tb-consumption",
                "limit": "15000000000000",
                "capacity_usage": "10000000000000",                
            },
            {
                "id": "102",
                "path": "/storage2/fs1/100tb-consumption",
                "limit": "100000000000000",
                "capacity_usage": "20",                
            },
            {
                "id": "103",
                "path": "/storage2/fs1/5tb-subscription",
                "limit": "5000000000000",
                "capacity_usage": "1",                
            },
            {
                "id": "104",
                "path": "/storage2/fs1/100tb-subscription",
                "limit": "100000000000000",
                "capacity_usage": "20",                
            },
            {
                "id": "105",
                "path": "/storage2/fs1/500tb-subscription",
                "limit": "500000000000000",
                "capacity_usage": "2",                
            },
            {
                "id": "106",
                "path": "/storage2/fs1/1000tb-subscription",
                "limit": "1000000000000000",
                "capacity_usage": "2",                
            },
            {
                "id": "107",
                "path": "/storage2/fs1/500tb-condo",
                "limit": "500000000000000",
                "capacity_usage": "2",                
            },
        ]
    }


class TestBillingReport(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        build_data = build_models()

        self.project = build_data["project"] # a project object from mock_data with project_name='Project 1'
        self.user = build_data["user"] # an user object from mock_data with username='test'

        self.storage_filesystem_path_attribute_type = AllocationAttributeType.objects.get(
            name="storage_filesystem_path"
        )
        self.storage_quota_attribute_type = AllocationAttributeType.objects.get(
            name="storage_quota"
        )
        return super().setUp()

    def test_header_return_csv(self):
        header = get_report_header()
        self.assertTrue(re.search("^Submit Internal Service Delivery(,){27}", header))
        self.assertEqual(
            hashlib.md5(header.encode('utf-8')).hexdigest(),
            '250225b6615daaa68b067ceef5abaf51'
        )
        
    def test_query_return_sql_statement(self):
        self.assertTrue(re.search("^\s*SELECT\s*", get_monthly_billing_query_template()))

    @patch("coldfront.plugins.qumulo.tasks.QumuloAPI")
    def test_create_an_allocation_and_ingest_usage(self, qumulo_api_mock: MagicMock) -> None:
        qumulo_api = MagicMock()
        qumulo_api.get_all_quotas_with_usage.return_value = mock_get_quotas_1()
        qumulo_api_mock.return_value = qumulo_api

    # def test_a_new_entry_in_database(self):
        create_allocation(
            project=self.project,
            user=self.user,
            form_data=set_allocation_form_data_with_5TB_consumption()
        )
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT count(*)
                FROM allocation_allocation a
                JOIN allocation_allocation_resources ar
                    ON ar.allocation_id=a.id
                JOIN resource_resource r
                    ON r.id=ar.resource_id
                WHERE r.name='Storage2';
            """)
            row = cursor.fetchone()
            self.assertEqual(1, row[0])

            # Exam the attributes of the new allocation
            cursor.execute("""
                SELECT aat.name, aa.value
                FROM allocation_allocation a
                JOIN allocation_allocationattribute aa
                    ON a.id=aa.allocation_id
                JOIN allocation_allocationattributetype aat
                    ON aa.allocation_attribute_type_id=aat.id;
            """)
            rows = cursor.fetchall()

        for row in rows: print(row)

        storage2_allocations = []
        for allocation in Allocation.objects.all():
            if (allocation.resources.first().name == 'Storage2'):
                storage2_allocations.append(allocation) 

        self.assertEqual(1, len(storage2_allocations))

        ingest_quotas_with_daily_usage()
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT aat.*, aau.value, aau.modified
                FROM allocation_allocationattributeusage aau
                JOIN allocation_allocationattribute aat
                    ON aat.id = aau.allocation_attribute_id;
            """) 
            rows = cursor.fetchall()

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT aa.allocation_id id,
                    aa.created,
                    storage_filesystem_path path,
                    aa.value quota,
                    aau.value now_usage,
                    ROUND(CAST(aau.value AS NUMERIC) /1024/1024/1024/1024, 2) now_usage_tb,
                    ROUND(CAST(haau.value AS NUMERIC) /1024/1024/1024/1024, 2) history_usage_tb,
                    haau.modified history_timestamp
                FROM allocation_allocationattributeusage aau
                JOIN allocation_allocationattribute aa
                    ON aa.id = aau.allocation_attribute_id
                JOIN allocation_historicalallocationattributeusage haau
                    ON aau.allocation_attribute_id = haau.allocation_attribute_id
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
                ORDER BY id DESC, history_timestamp DESC
            """) 
            rows = cursor.fetchall()

        for row in rows: print(row)

        print(datetime.today().strftime('%Y-%m-%d'))
        generate_monthly_billing_report(datetime.today().strftime('%Y-%m-%d'))

        filename = get_filename()
        self.assertFalse(re.search("RIS-%s-storage2-active-billing.csv", filename))
        self.assertTrue(re.search("RIS-[A-Za-z]+-storage2-active-billing.csv", filename))
        self.assertTrue(os.path.exists(filename))
        os.system(f'ls -l {filename}')


    @patch("coldfront.plugins.qumulo.tasks.QumuloAPI")
    def test_create_allocations_ingest_usages_generate_billing_report(self, qumulo_api_mock: MagicMock) -> None:
        qumulo_api = MagicMock()
        qumulo_api.get_all_quotas_with_usage.return_value = mock_get_quotas_2()
        qumulo_api_mock.return_value = qumulo_api

        allocations = [
            set_allocation_form_data_with_15TB_consumption,
            set_allocation_form_data_with_100TB_consumption,
            set_allocation_form_data_with_5TB_subscription,
            set_allocation_form_data_with_100TB_subscription,
            set_allocation_form_data_with_500TB_subscription,
            set_allocation_form_data_with_1000TB_subscription,
            set_allocation_form_data_with_500TB_condo,
        ]

        for allocation in allocations:
            create_allocation(
                project=self.project,
                user=self.user,
                form_data=allocation()
            )

        ingest_quotas_with_daily_usage()

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT aa.allocation_id id,
                    aa.created,
                    storage_filesystem_path path,
                    aa.value quota,
                    aau.value now_usage,
                    ROUND(CAST(aau.value AS NUMERIC) /1024/1024/1024/1024, 2) now_usage_tb,
                    ROUND(CAST(haau.value AS NUMERIC) /1024/1024/1024/1024, 2) history_usage_tb,
                    haau.modified history_timestamp
                FROM allocation_allocationattributeusage aau
                JOIN allocation_allocationattribute aa
                    ON aa.id = aau.allocation_attribute_id
                JOIN allocation_historicalallocationattributeusage haau
                    ON aau.allocation_attribute_id = haau.allocation_attribute_id
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
                ORDER BY id DESC, history_timestamp DESC
            """) 
            rows = cursor.fetchall()

        for row in rows: print(row)

        generate_monthly_billing_report(datetime.today().strftime('%Y-%m-%d'))

    # Test billing report with expected entires from the mock data
    #   Create mock data
    #     * allocations
    #   Ingest the mock data into the mock database
    #   Connect to the mock database
    #   Query mock database
    #   Generate report
    #   Validate the report for
    #     * consumption ratesk
    #     * subscription rates
    #     * condo rates

    # def test_generate_monthly_billing_report(self):
    #     self.assertTrue(generate_monthly_billing_report())