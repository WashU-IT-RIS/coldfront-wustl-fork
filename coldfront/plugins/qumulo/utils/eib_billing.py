import logging
import csv
from datetime import datetime, timedelta
from django.db import connection

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

YYYY_MM_DD = "%Y-%m-%d"

REPORT_HEADER = """Submit Internal Service Delivery,,,,,,,,,,,,,,,,,,,,,,,,,,,
Area,All,,Business Process Parameters,Internal Service Delivery Data,,,,,,,Internal Service Delivery Line Data+,,,,,,,,,,,,,
Restrictions,Required,Optional,Optional,Optional,Optional,Required,Required,Required,Required,Optional,Required,Optional,Required,Optional,Optional,Optional,Optional,Optional,Required,Optional,Optional,Optional,Optional. May have multiples,Optional. May have multiples
Format,Text,Y/N,Y/N,Text,Y/N,Company_Reference_ID,Internal_Service_Provider_ID,Currency_ID,YYYY-MM-DD,Text,Text,Text,Number,Text,Spend_Category_ID,Number (22,2),UN_CEFACT_Common_Code_ID,Number (26,6),Number (18,3),Employee_ID,YYYY-MM-DD,Text,Cost_Center_Reference_ID,Fund_ID
Fields,Spreadsheet Key*,Add Only,Auto Complete,Internal Service Delivery ID,Submit,Company*,Internal Service Provider*,Currency*,Document Date*,Memo,Row ID**,Internal Service Delivery Line ID,Internal Service Delivery Line Number*,Item Description,Spend Category,Quantity,Unit of Measure,Unit Cost,Extended Amount*,Requester,Delivery Date,Memo,Cost Center,Fund,,,,USAGE,RATE,UNIT
"""

QUERY_MONTHLY_BILLING = """
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
  'FY25 ' || '%s' || ' Monthly for ' || report.sponsor memo,
  '1' row_id,
  NULL internal_service_delivery_line_id,
  '1' internal_service_delivery_line_number,
  '"' || 'WashU IT RIS ' || report.service_name || ' - ' || report.service_rate_category || '; Usage: ' || report.billing_unit || ' X Rate: ' || report.rate || ' X Per: ' || report.service_unit || '"' item_description,
  'SC510' spend_category,
  '1' quantity,
  'EA' unit_of_measure,
  report.fee unit_cost,
  report.fee extended_amount,
  NULL requester,
  report.delivery_date delivery_date,
  '"' || report.storage_name || '"' fileset_memo,
  report.cost_center cost_center,
  NULL fund,
  NULL,
  NULL,
  NULL,
  report.billing_unit usage,
  report.rate rate,
  report.service_unit unit
FROM (
  SELECT
    '%s' delivery_date,
    data.service_unit,
    data.storage_name,
    data.service_name,
    data.sponsor,
    data.billing_unit,
    data.rate,
    data.service_rate_category,
    data.department_number,
    data.cost_center,
    data.billing_unit*data.rate fee
  FROM (
    SELECT
      DATE(most_recent_haau.recent_modified) usage_date,
      '1' service_id,
      department_number,
      storage_name,
      'Storage2 Active' service_name,
      u.username sponsor,
      service_rate_category,
      cost_center,
      'monthly' billing_cycle,
      true subsidized,
      false exempt,
      CASE service_rate_category
        WHEN 'consumption' THEN 13
        WHEN 'subscription' THEN 634
        WHEN 'subscription_500tb' THEN 2643
        WHEN 'condo' THEN 529
      END rate,
      storage_quota,
      CASE service_rate_category
        WHEN 'consumption' THEN (
          SELECT MAX(consumption_billing_unit)
          FROM (
            SELECT CAST(most_recent_haau.value AS FLOAT8) /1024/1024/1024/1024 -5 consumption_billing_unit
            UNION SELECT 0
          ) AS positive_billing_unit
        )
        WHEN 'subscription' THEN CEILING(CAST(storage_quota AS FLOAT8) /100)
        WHEN 'subscription_500tb' THEN CEILING(CAST(storage_quota AS FLOAT8) /500)
        WHEN 'condo' THEN CEILING(CAST(storage_quota AS FLOAT8) /500)
      END billing_unit,
      CASE service_rate_category
        WHEN 'consumption' THEN 'TB'
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
    JOIN (
      SELECT allocation_attribute_id,
        MAX(modified) recent_modified,
        value
      FROM allocation_historicalallocationattributeusage
      GROUP BY allocation_attribute_id, DATE(modified)
    ) AS most_recent_haau
      ON storage_quota.id=most_recent_haau.allocation_attribute_id
    JOIN allocation_allocation_resources ar ON ar.allocation_id=a.id
    JOIN resource_resource r ON r.id=ar.resource_id
    WHERE
      r.name = 'Storage2'
    AND
      DATE(most_recent_haau.recent_modified) = '%s'
    AND
      astatus.name = 'Active'
  ) AS data
) AS report where report.billing_unit > 0;
"""

filename = ""


def reset_filename() -> None:
    global filename
    filename = "/tmp/RIS-%s-storage2-active-billing.csv"


def get_filename() -> str:
    return filename


def get_report_header() -> str:
    return REPORT_HEADER


def get_monthly_billing_query_template() -> str:
    return QUERY_MONTHLY_BILLING


def generate_monthly_billing_report(
    usage_date=datetime.today().replace(day=1).strftime(YYYY_MM_DD),
) -> bool:
    # The date when the billing report was generated
    document_date = datetime.today().strftime("%m/%d/%Y")
    # The first day of the service month
    delivery_date = (
        (datetime.strptime(usage_date, YYYY_MM_DD).replace(day=1) - timedelta(1))
        .replace(day=1)
        .strftime(YYYY_MM_DD)
    )
    # The service month for billing
    billing_month = datetime.strptime(delivery_date, YYYY_MM_DD).strftime("%B")

    reset_filename()
    global filename
    # The temporary report file for the service month
    filename = get_filename() % billing_month

    monthly_billing_query = get_monthly_billing_query_template() % (
        document_date,
        billing_month,
        delivery_date,
        usage_date,
    )
    # logger.debug("Monthly billing query: %s", monthly_billing_query)

    try:
        with connection.cursor() as cursor:
            cursor.execute(monthly_billing_query)
            rows = cursor.fetchall()

    except Exception as e:
        logger.error("[Error] Database error: %s", e)
        logger.debug("Monthly billing query: %s", monthly_billing_query)
        return False

    file_handle = open(filename, "w")
    file_handle.write(get_report_header())
    file_handle.close()

    file_handle = open(filename, "a")
    billing_report = csv.writer(file_handle)
    billing_report.writerows(rows)
    file_handle.close()

    return True
