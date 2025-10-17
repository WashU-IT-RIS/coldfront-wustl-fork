from django.db import models

from coldfront.core.allocation.models import *
from coldfront.core.project.models import *
from coldfront.core.resource.models import *
from coldfront.core.user.models import *
from model_utils.models import TimeStampedModel
from simple_history.models import HistoricalRecords


class AllocationUsageQuerySet(models.QuerySet):

    def monthly_billable(self, usage_date):
        return self.filter(usage_date=usage_date,
                           exempt=False,
                           billing_cycle="monthly",
                           ).order_by()

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


    # From the queryset of monthly_billable consumption allocations
    def _count_subsidized_by_pi(self, sponsor_pi) -> int:
        return self.filter(
            sponsor_pi=sponsor_pi,
            subsidized=True,
        ).count()

    # From the queryset of monthly_billable consumption allocations
    def _is_all_subsidized_valid(self) -> bool:
        pis = self.values_list('sponsor_pi', flat=True).distinct()
        for pi in pis:
            if not self._is_subsidized_valid_by_pi(pi):
                return False  # Found a PI with more than one subsidized allocation
        return True

    # From the queryset of monthly_billable consumption allocations
    def _is_subsidized_valid_by_pi(self, sponsor_pi) -> bool:
        return self._count_subsidized_by_pi(sponsor_pi) <= 1
    
    # From the queryset of monthly_billable consumption allocations
    def set_and_validate_all_subsidized(self) -> bool:
        # breakpoint()
        if not self._is_all_subsidized_valid():
            return False  # Found a PI with more than one subsidized allocation

        pis = self.values_list('sponsor_pi', flat=True).distinct()
        for pi in pis:
            if self._count_subsidized_by_pi(pi) == 0:
                if not self._set_subsidized_by_pi(pi):
                    return False  # Failed to set subsidized allocation for this PI
        return self._is_all_subsidized_valid() 
        
    # From the queryset of monthly_billable consumption allocations
    def _set_subsidized_by_pi(self, sponsor_pi) -> bool:
        # No subsidized allocation for this PI, set the first one by external_key
        first_alloc = self.by_pi(sponsor_pi).order_by('external_key').first()
        if first_alloc:
            first_alloc.subsidized = True
            first_alloc.save()
            return True
        return False

    def manually_exempt_fileset(self, fileset_name):
        return self.filter(
            fileset_name!=fileset_name,
        )


class AllocationUsage(TimeStampedModel):
    """A usage table for allocations in all storage clusters for billing.

    Attribute:
        external_key (int): links to the primary key of the allocation to its source system
        source (str): indicates the source system of the usage (ex. ITSM, ColdFront)
        sponsor_pi (str): indicates who is primarily responsible for the allocation. Usually a WUSTLkey.
        billing_contact (str): indicates who is the main contact for billing issues
        fileset_name (str): represents the commonly used name of the allocation
        service_rate_category (str): indicates the billing rate of the allocation (ex. consumption, subscription, condo)
        usage_tb (str): indicates the consumption of the allocation in TB at the point of time, usage_date
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
            "usage_date",
            "sponsor_pi",
            "service_rate_category",
            "fileset_name",
        ]

        unique_together = (('storage_cluster', 'fileset_name', 'usage_date'),)

    external_key=models.IntegerField()
    source=models.CharField(max_length=256)
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
