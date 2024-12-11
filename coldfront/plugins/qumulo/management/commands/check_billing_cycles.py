import logging

from coldfront.config.env import ENV
from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttribute,
    AllocationAttributeType,
)
from coldfront.core.resource.models import Resource

from coldfront.plugins.qumulo.utils.aces_manager import AcesManager
from coldfront.plugins.qumulo.utils.qumulo_api import QumuloAPI
from coldfront.plugins.qumulo.utils.acl_allocations import AclAllocations
from coldfront.plugins.qumulo.utils.active_directory_api import ActiveDirectoryAPI
from django.db.models import OuterRef, Subquery

from qumulo.lib.request import RequestError

import time
from datetime import datetime

from typing import Optional

logger = logging.getLogger(__name__)


def calculate_prepaid_expiration(
    allocation, bill_cycle, prepaid_months, prepaid_billing_start, prepaid_expiration
) -> None:
    logger.warn(f"Calculation prepaid expiration")
    prepaid_exp_attribute = AllocationAttributeType.objects.get(
        name="prepaid_expiration"
    )
    if bill_cycle == "prepaid" and prepaid_expiration == None:
        prepaid_billing_start = datetime.strptime(prepaid_billing_start, "%Y-%m-%d")
        prepaid_months = int(prepaid_months)
        prepaid_until = datetime(
            prepaid_billing_start.year
            + (prepaid_billing_start.month + prepaid_months - 1) // 12,
            (prepaid_billing_start.month + prepaid_months - 1) % 12 + 1,
            prepaid_billing_start.day,
        )
        AllocationAttribute.objects.filter(
            allocation=allocation, allocation_attribute_type=prepaid_exp_attribute
        ).update(value=prepaid_until)
        logger.warn(f"{prepaid_expiration}")


def check_allocations() -> None:
    resource = Resource.objects.get(name="Storage2")
    allocations = Allocation.objects.filter(status__name="Active", resources=resource)
    billing_attribute = AllocationAttributeType.objects.get(name="billing_cycle")
    prepaid_exp_attribute = AllocationAttributeType.objects.get(
        name="prepaid_expiration"
    )
    prepaid_billing_start_attribute = AllocationAttributeType.objects.get(
        name="prepaid_billing_date"
    )
    prepaid_months_attribute = AllocationAttributeType.objects.get(name="prepaid_time")
    billing_sub_q = AllocationAttribute.objects.filter(
        allocation=OuterRef("pk"), allocation_attribute_type=billing_attribute
    ).values("value")[:1]
    prepaid_exp_sub_q = AllocationAttribute.objects.filter(
        allocation=OuterRef("pk"), allocation_attribute_type=prepaid_exp_attribute
    ).values("value")[:1]
    prepaid_billing_date_sub_q = AllocationAttribute.objects.filter(
        allocation=OuterRef("pk"),
        allocation_attribute_type=prepaid_billing_start_attribute,
    ).values("value")[:1]
    prepaid_months_sub_q = AllocationAttribute.objects.filter(
        allocation=OuterRef("pk"),
        allocation_attribute_type=prepaid_months_attribute,
    ).values("value")[:1]
    allocations = allocations.annotate(
        billing_cycle=Subquery(billing_sub_q),
        prepaid_expiration=Subquery(prepaid_exp_sub_q),
        prepaid_billing_start=Subquery(prepaid_billing_date_sub_q),
        prepaid_months=Subquery(prepaid_months_sub_q),
    )
    logger.warn(f"Checking billing_cycle in {len(allocations)} qumulo allocations")
    for allocation in allocations:
        logger.warn(f"{allocation.billing_cycle}")
        calculate_prepaid_expiration(
            allocation,
            allocation.billing_cycle,
            allocation.prepaid_months,
            allocation.prepaid_billing_start,
            allocation.prepaid_expiration,
        )

    # def conditionally_update_billing_cycle_types() -> None:
    #     logger.warn(
    #         f"Checking billing_cycle in {len(BillingCycleManager.allocations)} qumulo allocations"
    #     )
    #     for allocation in BillingCycleManager.allocations:
    #         if allocation.billing_cycle == "prepaid":
    #             if allocation.prepaid_expiration == datetime.today().strftime(
    #                 "%Y-%m-%d"
    #             ) or allocation.prepaid_expiration < datetime.today().strftime(
    #                 "%Y-%m-%d"
    #             ):
    #                 logger.warn(f"Changing {allocation} billing_cycle to monthly")
    #                 AllocationAttribute.objects.filter(
    #                     allocation=allocation,
    #                     allocation_attribute_type=BillingCycleManager.billing_attribute,
    #                 ).update(value="monthly")
    #         elif allocation.billing_cycle == "monthly":
    #             if allocation.prepaid_billing_start == datetime.today().strftime(
    #                 "%Y-%m-%d"
    #             ):
    #                 logger.warn(f"Changing {allocation} billing_cycle to prepaid")
    #                 logger.warn(f" {allocation.prepaid_billing_start} ")
    #                 AllocationAttribute.objects.filter(
    #                     allocation=allocation,
    #                     allocation_attribute_type=BillingCycleManager.billing_attribute,
    #                 ).update(value="prepaid")
