from django.db import models
from coldfront.core.allocation.models import *
from coldfront.core.project.models import *
from coldfront.core.resource.models import *
from coldfront.core.user.models import *
from model_utils.models import TimeStampedModel
from simple_history.models import HistoricalRecords

# Create your models here.

class AllocationUsage(TimeStampedModel):
    """A usage table for allocations in all storage clusters for billing.

    Attribute:
        external_key (int): links to the primary key of the allocation to its source system
        source (str): indicates the source system of the usage (ex. ITSM, ColdFront)
        sponsor_pi (str): indicates who is primarily responsible for the allocation
        billing_contact (str): indicates who is the main contact for billing issues
        fileset_name (str): represents the commonly used name of the allocation
        service_rate_category (str): indicates the billing rate of the allocation
        usage (str): indicates the consumption of the allocation in TB at a point of time
        funding_number (str): indicates the funding source aka cost center number
        exempt (bool): indicates if the fee is waived by RIS
        subsidized (bool): indicates if the allocation with consumption rate receives 5TB discount
        is_condo_group (bool): indicates if the allocation is a condo group parent
        parent_id_key (int): links to the external_key as its condo group parent, if applicable
        quota (str): indicates the quota of the allocation
        billing_cycle (str): indicates the billing cycle of the allocation
        usage_timestamp (Date): indicates the date of the recorded usage
        ingestion_date (Date): indicates the date of the ingestionķķ
        storage_cluster (str): indicates the cluster of the allocation (ex. storage1, storage2, storage3)
    """

    class Meta:
        ordering=[
            "usage_timestamp",
            "sponsor_pi",
            "service_rate_category",
        ]

    external_key=models.IntegerField()
    source=models.CharField(max_length=256)
    sponsor_pi=models.CharField(max_length=512)
    billing_contact=models.CharField(max_length=512)
    fileset_name=models.CharField(max_length=256)
    service_rate_category=models.CharField(max_length=256)
    usage=models.CharField(max_length=256)
    funding_number=models.CharField(max_length=256)
    exempt=models.BooleanField()
    subsidized=models.BooleanField()
    is_condo_group=models.BooleanField()
    parent_id_key=models.IntegerField()
    quota=models.CharField(max_length=256)
    billing_cycle=models.CharField(max_length=256)
    usage_timestamp=models.DateTimeField()
    ingestion_date=models.DateTimeField()
    storage_cluster=models.CharField(max_length=256)
    history = HistoricalRecords()
