import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy

from coldfront_plugin_qumulo.utils.active_directory_api import ActiveDirectoryAPI
from coldfront_plugin_qumulo.utils.qumulo_api import QumuloAPI


def validate_leading_forward_slash(value: str):
    if len(value) > 0 and value[0] != "/":
        raise ValidationError(
            message=gettext_lazy("%(value)s must start with '/'"),
            code="invalid",
            params={"value": value},
        )


def validate_parent_directory(value: str):
    qumulo_api = QumuloAPI()
    sub_directories = value.strip("/").split("/")

    for depth in range(1, len(sub_directories), 1):
        path = "/" + "/".join(sub_directories[0:depth])

        try:
            qumulo_api.rc.fs.get_acl_v2(path)
        except Exception as e:
            raise ValidationError(
                message=f"{path} does not exist.  Parent Allocations must first be made.",
                code="invalid",
            )


def _ad_user_validation_helper(ad_user: str) -> bool:
    active_directory_api = ActiveDirectoryAPI()

    try:
        active_directory_api.get_user(ad_user)
        return True
    except ValueError:
        return False


def validate_single_ad_user(ad_user: str):
    if not _ad_user_validation_helper(ad_user):
        raise ValidationError(message=ad_user, code="invalid")


def validate_single_ad_user_skip_admin(user: str):
    if user == "admin":
        return None
    return validate_single_ad_user(user)


def validate_ad_users(ad_users: list[str]):
    bad_users = []

    for user in ad_users:

        if not _ad_user_validation_helper(user):
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


def validate_ticket(ticket: str):
    if re.match("\d+$", ticket):
        return
    if re.match("ITSD-\d+$", ticket, re.IGNORECASE):
        return
    raise ValidationError(
        gettext_lazy("%(value)s must have format: ITSD-12345 or 12345"),
        params={"value": ticket},
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
