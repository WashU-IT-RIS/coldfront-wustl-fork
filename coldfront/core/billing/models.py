from datetime import datetime

from django.db import models

from coldfront.config.env import PROJECT_ROOT
from coldfront.core.allocation.models import *
from coldfront.core.project.models import *
from coldfront.core.resource.models import *
from coldfront.core.user.models import *
from model_utils.models import TimeStampedModel
from simple_history.models import HistoricalRecords


class AllocationUsageQuerySet(models.QuerySet):

    def monthly_billable(self, usage_date, tier="Active"):
        return self.filter(usage_date=usage_date,
                           tier=tier,
                           usage_tb__gt=0,
                           exempt=False,
                           billing_cycle="monthly",
                           ).exclude(
                               service_rate_category="condo",
                           )

    def with_usage_date(self, usage_date):
        return self.filter(usage_date=usage_date)

    def not_exempt(self):
        return self.filter(exempt=False)

    def consumption(self):
        return self.filter(
            service_rate_category="consumption",
        )

    def by_fileset(self, fileset_name):
        return self.filter(fileset_name=fileset_name)

    def by_pi(self, sponsor_pi):
        return self.filter(sponsor_pi=sponsor_pi)

    def only_positive_usage(self):
        return self.filter(usage_tb__gt=0)


    # From the queryset of monthly_billable consumption allocations
    def _count_subsidized_by_pi(self, sponsor_pi) -> int:
        return self.filter(
            sponsor_pi=sponsor_pi,
            subsidized=True,
        ).count()

    # From the queryset of monthly_billable consumption allocations
    def _is_all_subsidized_valid(self) -> bool:
        pis = self.values_list("sponsor_pi", flat=True).distinct()
        for pi in pis:
            if not self._is_subsidized_valid_by_pi(pi):
                return False  # Found a PI with more than one subsidized allocation
        return True

    # From the queryset of monthly_billable consumption allocations
    def _is_subsidized_valid_by_pi(self, sponsor_pi) -> bool:
        return self._count_subsidized_by_pi(sponsor_pi) <= 1
    
    # From the queryset of monthly_billable consumption allocations
    def set_and_validate_all_subsidized(self) -> bool:
        tier=self.first().tier
        if tier != "Active":
            self.all().update(subsidized=False)
            return True  # Only Active tier allocations are considered for subsidized setting

        if not self._is_all_subsidized_valid():
            return False  # Found a PI with more than one subsidized allocation

        pis = self.values_list("sponsor_pi", flat=True).distinct()
        for pi in pis:
            if self._count_subsidized_by_pi(pi) == 0:
                if not self._set_subsidized_by_pi(pi):
                    return False  # Failed to set subsidized allocation for this PI
        return self._is_all_subsidized_valid() 
        
    # From the queryset of monthly_billable consumption allocations
    def _set_subsidized_by_pi(self, sponsor_pi) -> bool:
        # No subsidized allocation for this PI, set the first one by external_key
        first_alloc = self.by_pi(sponsor_pi).order_by("external_key").first()
        if first_alloc:
            first_alloc.subsidized = True
            first_alloc.save()
            return True
        return False

    def manually_exempt_fileset(self, fileset_name):
        return self.exclude(
            fileset_name=fileset_name,
        )


class AllocationUsage(TimeStampedModel):
    """A usage table for allocations in all storage clusters for billing.

    Attribute:
        external_key (int): links to the primary key of the allocation to its source system
        source (str): indicates the source system of the usage (ex. ITSM, ColdFront)
        tier (str): indicates the service tier of the allocation (ex. Active, Archive)
        sponsor_pi (str): indicates who is primarily responsible for the allocation. Usually a WUSTLkey.
        billing_contact (str): indicates who is the main contact for billing issues
        fileset_name (str): represents the commonly used name of the allocation
        service_rate_category (str): indicates the billing rate of the allocation (ex. consumption, subscription, condo)
        usage_tb (decimal): indicates the consumption of the allocation in TB at the point of time, usage_date
        funding_number (str): indicates the funding source aka cost center number
        exempt (bool): indicates if the fee is waived by RIS
        subsidized (bool): indicates if the allocation with consumption rate will receive 5TB discount
        is_condo_group (bool): indicates if the allocation is a condo group parent
        parent_id_key (int): links to the external_key as its condo group parent, if applicable
        quota (str): indicates the quota of the allocation
        billing_cycle (str): indicates the billing cycle of the allocation (ex. monthly, prepaid)
        usage_date (Date): indicates the date of the recorded usage (ex. 2024-06-01)
        storage_cluster (str): indicates the cluster of the allocation (ex. storage1, storage2, storage3)
    """

    class Meta:
        ordering=[
            "tier",
            "usage_date",
            "sponsor_pi",
            "service_rate_category",
            "fileset_name",
        ]

        unique_together = (("tier", "storage_cluster", "fileset_name", "usage_date"),)

    external_key=models.IntegerField()
    source=models.CharField(max_length=256)
    tier=models.CharField(max_length=256)
    sponsor_pi=models.CharField(max_length=512)
    billing_contact=models.CharField(max_length=512)
    fileset_name=models.CharField(max_length=256)
    service_rate_category=models.CharField(max_length=256)
    usage_tb=models.DecimalField(max_digits=20, decimal_places=6)
    funding_number=models.CharField(max_length=256)
    exempt=models.BooleanField()
    subsidized=models.BooleanField()
    is_condo_group=models.BooleanField()
    parent_id_key=models.IntegerField(null=True, blank=True)
    quota=models.CharField(max_length=256)
    billing_cycle=models.CharField(max_length=256)
    usage_date=models.DateField()
    storage_cluster=models.CharField(max_length=256)
    objects = AllocationUsageQuerySet.as_manager()
    history = HistoricalRecords()


class MonthlyStorageBilling(AllocationUsage):
    """A data model for monthly storage billing.

    Additional Attributes Besides Those Inherited from AllocationUsage:
        *delivery_date (str): indicates the beginning date of the service for monthly billing (ex. 2024-05-01)
        *billable_usage_tb (str): indicates the billable usage in TB after applying subsidised discount if applicable
        *billing_unit (str): indicates the billing unit of the service (ex. TB)
        *unit_rate (str): indicates the unit rate of the service
        *billing_amount (str): indicates the total dollar amount of the service for the monthly billing
    """

    class Meta:
        managed = False  # This model does not create a database table

    HEADER_LINE_NO = 5
    # ISP: Internal Service Provider
    ISP_ACTIVE = "ISP0000030"
    ISP_ARCHIVE = "ISP0000199"
    # ISP_COMPUTE = "ISP0000370"


    @classmethod
    def _copy_template_headers_to_file(cls, template_filepath, target_filepath):
        """
        Copies the first line (header) from a template file to a target file.
        """
        try:
            # Read the template headers
            with open(template_filepath, "r") as template_file:
                headers = []
                for _ in range(cls.HEADER_LINE_NO):
                    line = template_file.readline().strip()  # Read a line and remove trailing whitespace
                    if not line:  # Handle cases where the template file has fewer than 5 lines
                        break
                    headers.append(line + "\n")

            # Write headers to output file
            with open(target_filepath, "w") as target_file:
                target_file.writelines(headers)

            print(f"Header successfully copied from '{template_filepath}' to '{target_filepath}'.")

        except FileNotFoundError:
            print("Error: One of the files was not found.")
        except Exception as e:
            print(f"An error occurred: {e}")

    @classmethod
    def _read_billing_entry_template(cls, template_filepath):
        """
        Reads and returns the template of billing entry from the template file.
        """

        billing_entry_line_no = cls.HEADER_LINE_NO + 1  # Line number where billing entry is expected
        try:
            with open(template_filepath, "r") as template_file:
                lines = template_file.readlines()
                if 0 < billing_entry_line_no <= len(lines):
                    billing_entry = lines[billing_entry_line_no - 1].strip()
                    return billing_entry
                else:
                    print("Error: Template file does not contain enough lines for billing entry.")
                    return None

        except FileNotFoundError:
            print("Error: Template file not found.")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None 

    @classmethod
    def _get_fiscal_year(cls, a_date):
        """
        Given a date, return the fiscal year as a combined string of
        'FY' and the last 2 digit of the year.
        Fiscal year starts on July 1st,
        """

        month = a_date.month
        fiscal_year = a_date.year
        if month >= 7:
            fiscal_year = a_date.year + 1

        return "FY" + str(fiscal_year)[-2:]

    @classmethod
    def _get_fiscal_year_by_delivery_date(cls, delivery_date):
        """
        This will be used in the memo filed in the billing report.
        The delivery date is the first date of the month when the service is delivered.
        """
        return cls._get_fiscal_year(delivery_date)

    @classmethod
    def _get_fiscal_year_by_document_date(cls, document_date):
        """
        This will be used in the Box folder name for storing the billing report.
        The document date is the date when the billing report is generated.
        """
        return cls._get_fiscal_year(document_date)

    @classmethod
    def _generate_report_filename(cls, a_tier, a_delivery_date):
        """
        Generate the billing report file name based on the tier and delivery date.
        Example: RIS-January-storage-active-billing.csv
        """
        month_name = a_delivery_date.strftime("%B")
        file_name = f"RIS-{month_name}-storage-{a_tier}-billing.csv"
        return file_name

    @classmethod
    def generate_report(cls, billing_objects, template_path=None, output_path=None):
        """
        Apply a list of monthly storage billing objects to the template and write to a CSV file.
        """
        # Read the template header
        if template_path is None:
            template_path = f"{PROJECT_ROOT()}/coldfront/core/billing/templates/RIS-monthly-storage-billing-template.csv"

        a_tier = billing_objects[0].tier
        a_delivery_date = datetime.strptime(billing_objects[0].delivery_date, "%Y-%m-%d")

        if output_path is None:
            output_filename = cls._generate_report_filename(a_tier, a_delivery_date)
            output_path = f"/tmp/{output_filename}"

        cls._copy_template_headers_to_file(template_path, output_path)

        # Build billing entries from the template
        billing_entry_template = cls._read_billing_entry_template(template_path)
        if not billing_entry_template:
            print("Error: Could not read billing entry template.")
            return

        if a_tier == "Active":
            ISP_code = cls.ISP_ACTIVE
        else:
            ISP_code = cls.ISP_ARCHIVE

        spreadsheet_key = 1
        document_date = datetime.now().date().strftime("%m/%d/%Y")
        fiscal_year = cls._get_fiscal_year_by_delivery_date(a_delivery_date)
        billing_month = a_delivery_date.strftime("%B")
        with open(output_path, "a") as output_file:
            for obj in billing_objects:
                # Replace placeholders in the template with actual values
                billing_entry = billing_entry_template.format(
                    spreadsheet_key=spreadsheet_key,
                    internal_service_provider=ISP_code,
                    document_date=document_date,
                    fiscal_year=fiscal_year,
                    billing_month=billing_month,
                    sponsor_pi=obj.sponsor_pi,
                    storage_cluster=obj.storage_cluster,
                    tier=obj.tier,
                    service_rate_category=obj.service_rate_category,
                    billable_usage_tb=obj.billable_usage_tb,
                    unit_rate=obj.unit_rate,
                    billing_unit=obj.billing_unit,
                    billing_amount=round(float(obj.billing_amount), 2),
                    delivery_date=obj.delivery_date,
                    fileset_name=obj.fileset_name,
                    funding_number=obj.funding_number,
                )
                output_file.write(billing_entry + "\n")
                spreadsheet_key += 1
