import logging
import csv
import re
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from django.db import connection

from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttribute,
    AllocationAttributeType,
)
from coldfront.plugins.qumulo.utils.billing_report import BillingReport

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

YYYY_MM_DD = "%Y-%m-%d"


class PrepaidBilling(BillingReport):
    def __init__(self, timestamp):
        super().__init__("prepaid", timestamp)

    def get_prepaid_billing_query_template(self) -> str:
        query_prepaid_billing = """
        SELECT
            NULL fields,
            ROW_NUMBER() OVER (ORDER BY report.service_name) spreadsheet_key,
            'N' add_only,
            'N' auto_complete,
            NULL internal_service_delivery_id,
            'Y' submit,
            'CP0001' company,
            'ISP0000030' internal_service_provider,
            'USD' currency,
            '%s' document_date,
            ('FY25 ' || '%s' || ' Prepaid for ' || report.sponsor) AS memo,
            '1' row_id,
            NULL internal_service_delivery_line_id,
            '1' internal_service_delivery_line_number,
            ('"' || 'WashU IT RIS ' || report.service_name || ' - ' || report.service_rate_category || '; Usage: ' || report.prepaid_time || ' X Rate: ' || report.rate || ' X Per: ' || report.service_unit || ' = Total Cost: ' || report.total_cost || '"') AS item_description,
            'SC510' spend_category,
            '1' quantity,
            'EA' unit_of_measure,
            report.billing_amount*report.rate unit_cost,
            report.billing_amount*report.rate extended_amount,
            NULL requester,
            report.delivery_date delivery_date,
            ('"' || report.storage_name || '"') AS fileset_memo,
            report.cost_center cost_center,
            report.prepaid_expiration prepaid_expiration,
            report.prepaid_time prepaid_time,
            NULL fund,
            NULL,
            NULL,
            NULL,
            report.rate rate,
            report.service_unit unit
        FROM (
            SELECT
                '%s' delivery_date,
                data.service_unit,
                data.storage_name,
                data.service_name,
                data.sponsor,
                CASE service_rate_category
                    WHEN 'consumption' THEN
                        CASE subsidized
                            WHEN TRUE THEN
                                CASE (billing_amount_tb - 5) > 0
                                    WHEN TRUE THEN (billing_amount_tb -5)
                                    ELSE 0
                                END
                            ELSE billing_amount_tb
                        END
                    ELSE billing_amount_tb
                END billing_amount,
                data.rate,
                data.service_rate_category,
                data.department_number,
                data.cost_center,
                data.prepaid_expiration,
                data.prepaid_time,
                data.rate * data.prepaid_time AS total_cost
            FROM (
                SELECT
                    '1' service_id,
                    department_number,
                    storage_name,
                    'Storage2 Active' service_name,
                    u.username sponsor,
                    service_rate_category,
                    cost_center,
                    prepaid_billing_date,
                    prepaid_expiration,
                    prepaid_time,
                    'monthly' billing_cycle,
                    TRUE subsidized,
                    FALSE exempt,
                    CASE service_rate_category
                        WHEN 'subscription' THEN 634
                        WHEN 'subscription_500tb' THEN 2643
                        WHEN 'condo' THEN 529
                    END rate,
                    storage_quota,
                    CASE service_rate_category
                        WHEN 'subscription' THEN CEILING(CAST(storage_quota AS FLOAT8) /100)
                        WHEN 'subscription_500tb' THEN CEILING(CAST(storage_quota AS FLOAT8) /500)
                        WHEN 'condo' THEN CEILING(CAST(storage_quota AS FLOAT8) /500)
                    END billing_amount_tb,
                    CASE service_rate_category
                        WHEN 'subscription' THEN '100TB'
                        WHEN 'subscription_500tb' THEN '500TB'
                        WHEN 'condo' THEN '500TB'
                    END service_unit,
                    storage_filesystem_path
                FROM allocation_allocation a
                JOIN allocation_allocationstatuschoice astatus ON a.status_id=astatus.id
                JOIN project_project p ON a.project_id=p.id
                JOIN auth_user u ON p.pi_id=u.id
                LEFT JOIN (SELECT aa.allocation_id, aa.value storage_name FROM allocation_allocationattribute aa JOIN allocation_allocationattributetype aat ON aa.allocation_attribute_type_id=aat.id WHERE aat.name='storage_name') AS storage_name ON a.id=storage_name.allocation_id
                LEFT JOIN (SELECT aa.allocation_id, aa.value storage_filesystem_path FROM allocation_allocationattribute aa JOIN allocation_allocationattributetype aat ON aa.allocation_attribute_type_id=aat.id WHERE aat.name='storage_filesystem_path') AS storage_filesystem_path ON a.id=storage_filesystem_path.allocation_id
                LEFT JOIN (SELECT aa.allocation_id, aa.value cost_center FROM allocation_allocationattribute aa JOIN allocation_allocationattributetype aat ON aa.allocation_attribute_type_id=aat.id WHERE aat.name='cost_center') AS cost_center ON a.id=cost_center.allocation_id
                LEFT JOIN (SELECT aa.allocation_id, aa.value department_number FROM allocation_allocationattribute aa JOIN allocation_allocationattributetype aat ON aa.allocation_attribute_type_id=aat.id WHERE aat.name='department_number') AS department_number ON a.id=department_number.allocation_id
                LEFT JOIN (SELECT aa.allocation_id, aa.value service_rate_category FROM allocation_allocationattribute aa JOIN allocation_allocationattributetype aat ON aa.allocation_attribute_type_id=aat.id WHERE aat.name='service_rate') AS service_rate_category ON a.id=service_rate_category.allocation_id
                LEFT JOIN (SELECT aa.allocation_id, aa.id, aa.value storage_quota FROM allocation_allocationattribute aa JOIN allocation_allocationattributetype aat ON aa.allocation_attribute_type_id=aat.id WHERE aat.name='storage_quota') AS storage_quota ON a.id=storage_quota.allocation_id
                LEFT JOIN (SELECT aa.allocation_id, aa.id, aa.value prepaid_billing_date FROM allocation_allocationattribute aa JOIN allocation_allocationattributetype aat ON aa.allocation_attribute_type_id=aat.id WHERE aat.name='prepaid_billing_date') AS prepaid_billing_date ON a.id=prepaid_billing_date.allocation_id
                LEFT JOIN (SELECT aa.allocation_id, aa.id, aa.value prepaid_expiration FROM allocation_allocationattribute aa JOIN allocation_allocationattributetype aat ON aa.allocation_attribute_type_id=aat.id WHERE aat.name='prepaid_expiration') AS prepaid_expiration ON a.id=prepaid_expiration.allocation_id
                LEFT JOIN (SELECT aa.allocation_id, aa.id, aa.value prepaid_time FROM allocation_allocationattribute aa JOIN allocation_allocationattributetype aat ON aa.allocation_attribute_type_id=aat.id WHERE aat.name='prepaid_time') AS prepaid_time ON a.id=prepaid_time.allocation_id
                JOIN allocation_allocation_resources ar ON ar.allocation_id=a.id
                JOIN resource_resource r ON r.id=ar.resource_id
                WHERE
                    r.name = 'Storage2'
                AND
                  astatus.name = 'Active'
            ) AS data
            WHERE prepaid_billing_date = '%s'
                AND exempt <> TRUE
        ) AS report 
        WHERE report.billing_amount > 0;
        """
        return query_prepaid_billing
    
    def _get_prepaid_billing_query(self) -> str:
        # The date when the billing report was generated
        document_date = datetime.today().strftime("%m/%d/%Y")

        prepaid_billing_query = self.get_prepaid_billing_query_template() % (
            document_date,
            self.billing_month,
            self.delivery_date,
            self.delivery_date,
        )
        return prepaid_billing_query

    def generate_prepaid_billing_report(self) -> bool:

        prepaid_billing_query = self._get_prepaid_billing_query()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                row = cursor.fetchone()

            logger.debug(f"[INFO] Database: {row[0]}")
            if re.search("mariadb", row[0], re.IGNORECASE):
                prepaid_billing_query = prepaid_billing_query.replace(
                    "('", "CONCAT('"
                ).replace("||", ",")

        except Exception as e:
            with connection.cursor() as cursor:
                cursor.execute("SELECT sqlite_version();")
                row = cursor.fetchone()

            logger.debug(f"[INFO] Database: sqlite version {row[0]}")

        try:
            with connection.cursor() as cursor:
                cursor.execute(prepaid_billing_query)
                rows = cursor.fetchall()

        except Exception as e:
            logger.error("[Error] Database error: %s", e)
            logger.debug("Prepaid billing query: %s", prepaid_billing_query)
            return False

        try:
            file_handle = open(self.filename, "w")
            file_handle.write(self.get_report_header())
            file_handle.close()

            file_handle = open(self.filename, "a")
            billing_report = csv.writer(file_handle)
            billing_report.writerows(rows)
            file_handle.close()

        except Exception as e:
            logger.error("[Error] Write file error: %s", e)
            logger.debug("Filename: %s" % self.filename)
            return False

        return True