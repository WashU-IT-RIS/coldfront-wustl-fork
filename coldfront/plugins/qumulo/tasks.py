from django.db.models import Q
from django.contrib.auth.models import User
from django_q.tasks import async_task
import logging
import os

from coldfront.config.env import ENV
from coldfront.core.allocation.models import (
    Allocation,
    AllocationStatusChoice,
    AllocationAttribute,
    AllocationAttributeType,
    AllocationAttributeUsage,
)
from coldfront.core.resource.models import Resource
from coldfront.core.utils.mail import send_email_template, email_template_context
from coldfront.core.utils.common import import_from_settings

from coldfront.plugins.qumulo.utils.qumulo_api import QumuloAPI
from coldfront.plugins.qumulo.utils.acl_allocations import AclAllocations
from coldfront.plugins.qumulo.utils.active_directory_api import ActiveDirectoryAPI

from qumulo.lib.request import RequestError

import time
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)
SECONDS_IN_AN_HOUR = 60 * 60
SECONDS_IN_A_DAY = 24 * SECONDS_IN_AN_HOUR


def poll_ad_group(
    acl_allocation: Allocation,
    expiration_seconds: int = SECONDS_IN_A_DAY,
) -> None:
    qumulo_api = QumuloAPI()

    storage_acl_name = acl_allocation.get_attribute("storage_acl_name")
    group_dn = ActiveDirectoryAPI.generate_group_dn(storage_acl_name)

    success = False

    try:
        qumulo_api.rc.ad.distinguished_name_to_ad_account(group_dn)
        success = True
    except RequestError:
        logger.warn(f'Allocation Group "{group_dn}" not found')
        success = False

    acl_group_name = acl_allocation.get_attribute("storage_acl_name")
    time_since_creation = time.time() - acl_allocation.created.timestamp()

    if success:
        acl_allocation.status = AllocationStatusChoice.objects.get(name="Active")
        logger.warn(f'Allocation Group "{acl_group_name}" found')
    elif time_since_creation > expiration_seconds:
        logger.warn(
            f'Allocation Group "{acl_group_name}" not found after {expiration_seconds/SECONDS_IN_AN_HOUR} hours'
        )
        acl_allocation.status = AllocationStatusChoice.objects.get(name="Expired")

    acl_allocation.save()


def poll_ad_groups() -> None:
    resources = Resource.objects.filter(Q(name="rw") | Q(name="ro"))
    acl_allocations = Allocation.objects.filter(
        status__name="Pending", resources__in=resources
    )

    logger.warn(f"Polling {len(acl_allocations)} ACL allocations")

    for acl_allocation in acl_allocations:
        poll_ad_group(acl_allocation)


def conditionally_update_storage_allocation_status(allocation: Allocation) -> None:
    acl_allocations = AclAllocations.get_access_allocations(allocation)

    for acl_allocation in acl_allocations:
        if acl_allocation.status.name != "Active":
            return

    allocation.status = AllocationStatusChoice.objects.get(name="New")
    allocation.save()


def conditionally_update_storage_allocation_statuses() -> None:
    resource = Resource.objects.get(name="Storage2")
    allocations = Allocation.objects.filter(status__name="Pending", resources=resource)
    logger.warn(f"Checking {len(allocations)} qumulo allocations")

    for allocation in allocations:
        conditionally_update_storage_allocation_status(allocation)


def ingest_quotas_with_daily_usage() -> None:
    logger = logging.getLogger("task_qumulo_daily_quota_usages")

    quota_usages = __get_quota_usages_from_qumulo(logger)
    __set_daily_quota_usages(quota_usages, logger)
    __validate_results(quota_usages, logger)


def addUsersToADGroup(
    wustlkeys: list[str],
    acl_allocation: Allocation,
    bad_keys: Optional[list[str]] = None,
    good_keys: Optional[list[dict]] = None,
) -> None:
    if bad_keys is None:
        bad_keys = []
    if good_keys is None:
        good_keys = []

    if len(wustlkeys) == 0:
        return __ad_users_and_handle_errors(
            wustlkeys, acl_allocation, good_keys, bad_keys
        )

    active_directory_api = ActiveDirectoryAPI()
    wustlkey = wustlkeys[0]

    user = None
    success = False
    try:
        user = active_directory_api.get_user(wustlkey)
        success = True
    except ValueError:
        bad_keys.append(wustlkey)
        success = False

    if success:
        good_keys.append({"wustlkey": wustlkey, "dn": user["dn"]})

    async_task(addUsersToADGroup, wustlkeys[1:], acl_allocation, bad_keys, good_keys)


def __ad_users_and_handle_errors(
    wustlkeys: list[str],
    acl_allocation: Allocation,
    good_keys: list[dict],
    bad_keys: list[str],
) -> None:
    active_directory_api = ActiveDirectoryAPI()
    group_name = acl_allocation.get_attribute("storage_acl_name")

    if len(good_keys) > 0:
        user_dns = [user["dn"] for user in good_keys]
        try:
            active_directory_api.add_user_dns_to_ad_group(user_dns, group_name)
        except Exception as e:
            logger.error(f"Error adding users to AD group: {e}")
            __send_error_adding_users_email(acl_allocation)
            return

        for user in good_keys:
            AclAllocations.add_user_to_access_allocation(
                user["wustlkey"], acl_allocation
            )
    if len(bad_keys) > 0:
        __send_invalid_users_email(acl_allocation, bad_keys)
    return


def __send_error_adding_users_email(acl_allocation: Allocation) -> None:
    ctx = email_template_context()

    CENTER_BASE_URL = import_from_settings("CENTER_BASE_URL")
    ctx["allocation_url"] = f"{CENTER_BASE_URL}/allocation/{acl_allocation.id}"
    ctx["access_type"] = (
        "Read Only" if acl_allocation.resources.first().name == "ro" else "Read Write"
    )

    user_support_users = User.objects.filter(groups__name="RIS_UserSupport")
    user_support_emails = [user.email for user in user_support_users if user.email]

    send_email_template(
        subject="Error adding users to Storage Allocation",
        template_name="email/error_adding_users.txt",
        template_context=ctx,
        sender=import_from_settings("DEFAULT_FROM_EMAIL"),
        receiver_list=user_support_emails,
    )


def __send_invalid_users_email(acl_allocation: Allocation, bad_keys: list[str]) -> None:
    ctx = email_template_context()

    CENTER_BASE_URL = import_from_settings("CENTER_BASE_URL")
    ctx["allocation_url"] = f"{CENTER_BASE_URL}/allocation/{acl_allocation.id}"
    ctx["access_type"] = (
        "Read Only" if acl_allocation.resources.first().name == "ro" else "Read Write"
    )
    ctx["invalid_users"] = bad_keys

    user_support_users = User.objects.filter(groups__name="RIS_UserSupport")
    user_support_emails = [user.email for user in user_support_users if user.email]

    send_email_template(
        subject="Users not found in Storage Allocation",
        template_name="email/invalid_users.txt",
        template_context=ctx,
        sender=import_from_settings("DEFAULT_FROM_EMAIL"),
        receiver_list=user_support_emails,
    )


def __get_quota_usages_from_qumulo(logger):
    qumulo_api = QumuloAPI()
    quota_usages = qumulo_api.get_all_quotas_with_usage()
    return quota_usages


def __set_daily_quota_usages(all_quotas, logger) -> None:
    # Iterate and populate allocation_attribute_usage records
    storage_filesystem_path_attribute_type = AllocationAttributeType.objects.get(
        name="storage_filesystem_path"
    )
    for quota in all_quotas["quotas"]:
        path = quota.get("path")

        allocation = __get_allocation_by_attribute(
            storage_filesystem_path_attribute_type, path
        )
        if allocation is None:
            if path[-1] != "/":
                continue

            value = path[:-1]
            logger.warn(f"Attempting to find allocation without the trailing slash...")
            allocation = __get_allocation_by_attribute(
                storage_filesystem_path_attribute_type, value
            )
            if allocation is None:
                continue

        allocation.set_usage("storage_quota", quota.get("capacity_usage"))


def __get_allocation_by_attribute(attribute_type, value):
    try:
        attribute = AllocationAttribute.objects.get(
            value=value, allocation_attribute_type=attribute_type
        )
    except AllocationAttribute.DoesNotExist:
        logger.warn(f"Allocation record for {value} path was not found")
        return None

    logger.warn(f"Allocation record for {value} path was found")
    return attribute.allocation


def __validate_results(quota_usages, logger) -> bool:
    today = datetime.today()
    year = today.year
    month = today.month
    day = today.day

    daily_usage_ingested = AllocationAttributeUsage.objects.filter(
        modified__year=year, modified__month=month, modified__day=day
    ).count()
    usage_pulled_from_qumulo = len(quota_usages["quotas"])

    logger.info("Usages ingested for today: ", daily_usage_ingested)
    logger.info("Usages pulled from QUMULO: ", usage_pulled_from_qumulo)

    success = usage_pulled_from_qumulo == daily_usage_ingested
    if success:
        logger.warn("Successful ingestion of quota daily usage.")
    else:
        logger.warn("Unsuccessful ingestion of quota daily usage. Check the results.")

    return success
