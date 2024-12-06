from django.dispatch import receiver
from django_q.tasks import async_task

import logging
import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from coldfront.plugins.qumulo.utils.qumulo_api import QumuloAPI
from coldfront.plugins.qumulo.utils.acl_allocations import AclAllocations
from coldfront.plugins.qumulo.tasks import reset_allocation_acls


from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttribute,
    AllocationAttributeType,
)
from coldfront.core.allocation.signals import (
    allocation_activate,
    allocation_disable,
    allocation_change_approved,
)


from django.contrib.auth.models import User
from django.db.models.signals import post_save

from coldfront.plugins.qumulo.utils.update_user_data import (
    update_user_with_additional_data,
)

import sys


@receiver(post_save, sender=User)
def on_allocation_save_retrieve_additional_user_data(
    sender, instance, created, **kwargs
):
    if created and "admin" not in instance.username:
        _ = update_user_with_additional_data(instance.username)


@receiver(allocation_activate)
def on_allocation_activate(sender, **kwargs):
    logger = logging.getLogger(__name__)
    qumulo_api = QumuloAPI()

    allocation = Allocation.objects.get(pk=kwargs["allocation_pk"])

    fs_path = allocation.get_attribute(name="storage_filesystem_path")
    export_path = allocation.get_attribute(name="storage_export_path")
    protocols = json.loads(allocation.get_attribute(name="storage_protocols"))
    name = allocation.get_attribute(name="storage_name")
    limit_in_bytes = allocation.get_attribute(name="storage_quota") * (2**40)
    bill_cycle = allocation.get_attribute(name="billing_cycle")
    allocation_attribute_obj_type = AllocationAttributeType.objects.get(
        name="prepaid_expiration"
    )
    prepaid_billing_start = allocation.get_attribute(name="prepaid_billing_date")
    if bill_cycle == "prepaid":
        prepaid_months = allocation.get_attribute(name="prepaid_time")
        # prepaid_billing_start = datetime.strptime(prepaid_billing_start, "%Y-%m-%d")
        prepaid_until = datetime(
            prepaid_billing_start.year
            + (prepaid_billing_start.month + prepaid_months - 1) // 12,
            (prepaid_billing_start.month + prepaid_months - 1) % 12 + 1,
            prepaid_billing_start.day,
        )

    else:
        prepaid_until = datetime.today().strftime("%Y-%m-%d")

    AllocationAttribute.objects.get_or_create(
        allocation_attribute_type=allocation_attribute_obj_type,
        allocation=allocation,
        value=prepaid_until,
    )
    fs_path = allocation.get_attribute(name="storage_filesystem_path")
    export_path = allocation.get_attribute(name="storage_export_path")
    protocols = json.loads(allocation.get_attribute(name="storage_protocols"))
    name = allocation.get_attribute(name="storage_name")
    limit_in_bytes = allocation.get_attribute(name="storage_quota") * (2**40)

    try:
        # Create allocation
        qumulo_api.create_allocation(
            protocols=protocols,
            export_path=export_path,
            fs_path=fs_path,
            name=name,
            limit_in_bytes=limit_in_bytes,
        )

        qumulo_api.setup_allocation(fs_path)

    except ValueError:
        logger.warn("Can't create allocation: Some attributes are missing or invalid")

    AclAllocations.set_allocation_acls(allocation, qumulo_api)

    if QumuloAPI.is_allocation_root_path(fs_path):
        qumulo_api.create_allocation_readme(fs_path)

    async_task(
        reset_allocation_acls,
        "",
        allocation,
        False,
        q_options={"retry": 90000, "timeout": 86400},
    )


@receiver(allocation_disable)
def on_allocation_disable(sender, **kwargs):
    allocation = Allocation.objects.get(pk=kwargs["allocation_pk"])

    AclAllocations.remove_acl_access(allocation)


@receiver(allocation_change_approved)
def on_allocation_change_approved(sender, **kwargs):
    qumulo_api = QumuloAPI()
    allocation_obj = Allocation.objects.get(pk=kwargs["allocation_pk"])

    fs_path = allocation_obj.get_attribute(name="storage_filesystem_path")
    export_path = allocation_obj.get_attribute(name="storage_export_path")
    protocols = json.loads(allocation_obj.get_attribute(name="storage_protocols"))
    name = allocation_obj.get_attribute(name="storage_name")
    limit_in_bytes = allocation_obj.get_attribute(name="storage_quota") * (2**40)

    qumulo_api.update_allocation(
        protocols=protocols,
        export_path=export_path,
        fs_path=fs_path,
        name=name,
        limit_in_bytes=limit_in_bytes,
    )
