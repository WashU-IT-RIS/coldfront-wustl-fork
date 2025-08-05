import os
import re
import json

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy

from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttribute,
    AllocationAttributeType,
    AllocationStatusChoice,
)

from coldfront.plugins.qumulo.utils.active_directory_api import ActiveDirectoryAPI
from coldfront.plugins.qumulo.utils.qumulo_api import QumuloAPI
from coldfront.plugins.qumulo.utils.storage_controller import StorageControllerFactory

from pathlib import PurePath
from qumulo.lib import request
from datetime import date


def validate_ad_users(ad_users: list[str]):
    active_directory_api = ActiveDirectoryAPI()

    bad_users = []

    gotten_users = active_directory_api.get_members(ad_users)
    gotten_user_names = [user["attributes"]["sAMAccountName"] for user in gotten_users]

    for user in ad_users:
        if user not in gotten_user_names:
            bad_users.append(user)

    if len(bad_users) > 0:
        raise ValidationError(
            list(
                map(
                    lambda bad_user: ValidationError(message=bad_user, code="invalid"),
                    bad_users,
                )
            )
        )


def validate_filesystem_path_unique(value: str, resource_type: str):
    connection_info = json.loads(os.environ.get("QUMULO_INFO"))
    storage_dir = connection_info[resource_type]["path"].strip("/")
    full_path = f"/{storage_dir}/{value}"
    qumulo_api = StorageControllerFactory().create_connection(resource_type)

    reserved_statuses = AllocationStatusChoice.objects.filter(
        name__in=["Pending", "Active", "New"]
    )
    storage_filesystem_path_attribute_type = AllocationAttributeType.objects.get(
        name="storage_filesystem_path"
    )
    allocations = list(
        Allocation.objects.filter(
            allocationattribute__allocation_attribute_type=storage_filesystem_path_attribute_type,
            allocationattribute__value=full_path,
            status__in=reserved_statuses,
        )
    )

    if allocations:
        raise ValidationError(
            message=f"The entered path ({full_path}) already exists",
            code="invalid",
        )

    path_exists = True
    try:
        attr = qumulo_api.rc.fs.get_file_attr(full_path)
    except request.RequestError:
        path_exists = False

    if path_exists is True:
        raise ValidationError(
            message=f"The entered path ({full_path}) already exists",
            code="invalid",
        )


def validate_ldap_usernames_and_groups(name: str):
    if name is None:
        return

    if re.match("^(?=\s*$)", name):
        return

    if __ldap_usernames_and_groups_validator(name):
        return True

    raise ValidationError(
        gettext_lazy(
            "The name \"%(name)\" must not include '(', ')', '@', '/', or end with a period."
        ),
        params={"name": name},
    )


def validate_leading_forward_slash(value: str):
    if len(value) > 0 and value[0] != "/":
        raise ValidationError(
            message=gettext_lazy("%(value)s must start with '/'"),
            code="invalid",
            params={"value": value},
        )


def validate_parent_directory(value: str):

    storage_root = os.environ.get("STORAGE2_PATH").strip("/")
    full_path = f"/{storage_root}/{value}"
    qumulo_api = StorageControllerFactory().create_connection("Storage2")
    sub_directories = full_path.strip("/").split("/")

    for depth in range(1, len(sub_directories), 1):
        path = "/" + "/".join(sub_directories[0:depth])

        try:
            qumulo_api.rc.fs.get_file_attr(path)
        except Exception as e:
            raise ValidationError(
                message=f"{path} does not exist.  Parent Allocations must first be made.",
                code="invalid",
            )


def validate_single_ad_user(ad_user: str):
    if not __ad_user_validation_helper(ad_user):
        raise ValidationError(
            message="This WUSTL Key could not be validated", code="invalid"
        )


def validate_single_ad_user_skip_admin(user: str):
    if user == "admin":
        return None
    return validate_single_ad_user(user)


def validate_single_ad_user_skip_admin(user: str):
    if user == "admin":
        return None
    return validate_single_ad_user(user)


def validate_storage_name(value: str):
    valid_character_match = re.match("^[0-9a-zA-Z\-_\.]*$", value)

    if not valid_character_match:
        raise ValidationError(
            message=gettext_lazy(
                "Storage name must contain only alphanumeric characters, hyphens, underscores, and periods."
            ),
            code="invalid",
        )

    existing_allocations = AllocationAttribute.objects.filter(
        allocation_attribute_type__name="storage_name", value=value
    )

    if existing_allocations.first():
        raise ValidationError(message=f"{value} already exists", code="invalid")

    return


def validate_relative_path(value: str):
    path = PurePath(value)
    if PurePath(value).is_absolute() or len(path.parts) != 1:
        raise ValidationError(
            message=gettext_lazy("Only relative paths with no slashes are allowed"),
            code="invalid",
        )


def validate_ticket(ticket: str):
    if re.match("\d+$", ticket):
        return
    if re.match("ITSD-\d+$", ticket, re.IGNORECASE):
        return
    raise ValidationError(
        gettext_lazy("%(value)s must have format: ITSD-12345 or 12345"),
        params={"value": ticket},
    )


def validate_prepaid_start_date(prepaid_billing_date: date):
    start_day = prepaid_billing_date.day
    if start_day != 1:
        raise ValidationError(
            gettext_lazy("Prepaid billing can only start on the first of the month")
        )
    return


def __ad_user_validation_helper(ad_user: str) -> bool:
    active_directory_api = ActiveDirectoryAPI()

    try:
        active_directory_api.get_user(ad_user)
        return True
    except ValueError:
        return False


# documentation https://www.ibm.com/docs/en/sva/10.0.8?topic=names-characters-disallowed-user-group-name
def __ldap_usernames_and_groups_validator(name: str) -> bool:
    for token in ["(", ")", "@", "/"]:
        if name.__contains__(token):
            return False

    for index, chr in enumerate(name):
        if chr in list(["+", ";", ",", "<", ">", "#"]):
            escaped = index > 0 and (name[index - 1] == "\\")
            if not escaped:
                return False

    index = 0
    name_length = len(name)
    while index < name_length:
        if chr == "\\":
            escaped = (index < name_length) and (
                name[index + 1] in list(["+", ";", ",", "<", ">", "#", "\\"])
            )
            if not escaped:
                return False
            index = index + 1

        index = index + 1

    if name[-1] == ".":
        return False

    return True
