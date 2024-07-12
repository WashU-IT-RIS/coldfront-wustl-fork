from coldfront_plugin_qumulo.utils.active_directory_api import ActiveDirectoryAPI
from typing import Optional

from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttribute,
    AllocationAttributeType,
    AllocationStatusChoice,
    Resource,
    AllocationUserStatusChoice,
    AllocationUser,
    User,
)

from coldfront_plugin_qumulo.utils.qumulo_api import QumuloAPI
from coldfront_plugin_qumulo.utils.deafult_aces import default_aces

from ldap3.core.exceptions import LDAPException
from qumulo.lib.request import RequestError

import time


class AclAllocations:
    def __init__(self, project_pk):
        self.project_pk = project_pk

    def add_allocation_users(self, allocation: Allocation, wustlkeys: list):
        for wustlkey in wustlkeys:
            AllocationUser.objects.get_or_create(
                status=AllocationUserStatusChoice.objects.get(name="Active"),
                user=User.objects.get(username=wustlkey),
                allocation=allocation,
            )

    @staticmethod
    def add_user_to_access_allocation(username: str, allocation: Allocation):
        # NOTE - just need to provide the proper username
        # post_save handler will retrieve email, given/surname, etc.
        user_tuple = User.objects.get_or_create(username=username)

        AllocationUser.objects.create(
            allocation=allocation,
            user=user_tuple[0],
            status=AllocationUserStatusChoice.objects.get(name="Active"),
        )

    def create_acl_allocation(
        self, acl_type: str, users: list, active_directory_api=None
    ):
        allocation = Allocation.objects.create(
            project=self.project_pk,
            justification="",
            quantity=1,
            status=AllocationStatusChoice.objects.get(name="Active"),
        )

        resource = Resource.objects.get(name=acl_type)

        allocation.resources.add(resource)

        self.add_allocation_users(allocation=allocation, wustlkeys=users)
        self.set_allocation_attributes(
            allocation=allocation, acl_type=acl_type, wustlkey=users[0]
        )

        try:
            self.create_ad_group_and_add_users(
                wustlkeys=users,
                allocation=allocation,
                active_directory_api=active_directory_api,
            )
        except LDAPException as e:
            Allocation.delete(allocation)

    def create_acl_allocations(self, ro_users: list, rw_users: list):
        active_directory_api = ActiveDirectoryAPI()

        self.create_acl_allocation(
            acl_type="ro", users=ro_users, active_directory_api=active_directory_api
        )
        self.create_acl_allocation(
            acl_type="rw", users=rw_users, active_directory_api=active_directory_api
        )

    @staticmethod
    def create_ad_group_and_add_users(
        wustlkeys: list,
        allocation: Allocation,
        active_directory_api: Optional[ActiveDirectoryAPI] = None,
    ) -> None:
        if not active_directory_api:
            active_directory_api = ActiveDirectoryAPI()

        group_name = allocation.get_attribute(name="storage_acl_name")

        active_directory_api.create_ad_group(group_name)

        for wustlkey in wustlkeys:
            active_directory_api.add_user_to_ad_group(
                wustlkey=wustlkey, group_name=group_name
            )

    @staticmethod
    def extend_parent_acl(fs_path: str, extra_aces: list, qumulo_api: QumuloAPI):
        existing_acl = qumulo_api.rc.fs.get_acl_v2(fs_path)

        existing_acl["aces"].extend(extra_aces)

        qumulo_api.rc.fs.set_acl_v2(acl=existing_acl, path=fs_path)

        is_root_path = len(fs_path.strip("/").split("/")) == 1
        if not is_root_path:
            parent_path = "/" + "/".join(fs_path.strip("/").split("/")[0:-1])
            AclAllocations.extend_parent_acl(parent_path, extra_aces, qumulo_api)

    @staticmethod
    def get_access_allocation(storage_allocation: Allocation, resource_name: str):
        def filter_func(access_allocation: Allocation):
            try:
                access_allocation.resources.get(name=resource_name)
            except:
                return False

            return True

        access_allocations = AclAllocations.get_access_allocations(storage_allocation)

        access_allocation = next(
            filter(
                filter_func,
                access_allocations,
            ),
            None,
        )

        return access_allocation

    @staticmethod
    def get_access_allocations(qumulo_allocation: Allocation) -> list[Allocation]:
        project_access_allocations = Allocation.objects.filter(
            project=qumulo_allocation.project
        )

        access_allocations = filter(
            lambda access_allocation: access_allocation.get_attribute(
                name="storage_allocation_pk"
            )
            == qumulo_allocation.pk,
            project_access_allocations,
        )

        return list(access_allocations)

    @staticmethod
    def remove_acl_access(allocation: Allocation):
        qumulo_api = QumuloAPI()
        acl_allocations = AclAllocations.get_access_allocations(allocation)
        fs_path = allocation.get_attribute(name="storage_filesystem_path")

        for acl_allocation in acl_allocations:
            acl = qumulo_api.rc.fs.get_acl_v2(fs_path)

            group_name = acl_allocation.get_attribute(name="storage_acl_name")

            filtered_aces = filter(
                lambda ace: ace["trustee"]["name"] != group_name, acl["aces"]
            )

            acl["aces"] = list(filtered_aces)

            qumulo_api.rc.fs.set_acl_v2(acl=acl, path=fs_path)

            acl_allocation.status = AllocationStatusChoice.objects.get(name="Revoked")
            acl_allocation.save()

    def set_allocation_attributes(
        self, allocation: Allocation, acl_type: str, wustlkey: str
    ):
        allocation_attribute_type = AllocationAttributeType.objects.get(
            name="storage_acl_name"
        )

        AllocationAttribute.objects.create(
            allocation_attribute_type=allocation_attribute_type,
            allocation=allocation,
            value=f"storage-{wustlkey}-{acl_type}",
        )

    @staticmethod
    def set_qumulo_acls(
        base_allocation: Allocation,
        qumulo_api: QumuloAPI,
    ):
        access_allocations = AclAllocations.get_access_allocations(base_allocation)

        extra_aces = []

        for access_allocation in access_allocations:
            extra_aces.extend(get_extra_aces(access_allocation))

        fs_path: str = base_allocation.get_attribute("storage_filesystem_path")
        is_root_path = len(fs_path.strip("/").split("/")) == 1

        aces = extra_aces.copy()

        if is_root_path:
            aces.extend(default_aces.copy())
        else:
            initial_acl = qumulo_api.rc.fs.get_acl_v2(fs_path)
            aces.extend(initial_acl["aces"])

        acl = {"control": ["PRESENT"], "posix_special_permissions": [], "aces": aces}

        errors = []
        suceeded = False

        retry_delay = 5
        num_retries = 3
        for try_number in range(num_retries):
            try:
                qumulo_api.rc.fs.set_acl_v2(acl=acl, path=fs_path)
                suceeded = True
                break
            except RequestError as request_error:
                errors.append(request_error)
                time.sleep(retry_delay)

        if not suceeded:
            raise Exception(errors)

        if not is_root_path:
            parent_path = "/" + "/".join(fs_path.strip("/").split("/")[0:-1])
            AclAllocations.extend_parent_acl(parent_path, extra_aces, qumulo_api)


def get_extra_aces(access_allocation: Allocation):
    group_name = access_allocation.get_attribute(name="storage_acl_name")

    dir_ace = {
        "flags": ["CONTAINER_INHERIT"],
        "type": "ALLOWED",
        "trustee": {"name": group_name, "domain": "ACTIVE_DIRECTORY"},
        "rights": [
            "READ",
            "SYNCHRONIZE",
            "READ_ACL",
            "READ_ATTR",
            "READ_EA",
            "EXECUTE",
        ],
    }

    file_ace = {
        "flags": ["OBJECT_INHERIT"],
        "type": "ALLOWED",
        "trustee": {"name": group_name, "domain": "ACTIVE_DIRECTORY"},
        "rights": [
            "READ",
            "SYNCHRONIZE",
            "READ_ACL",
            "READ_ATTR",
            "READ_EA",
        ],
    }

    if access_allocation.resources.filter(name="rw").exists():
        rw_rights = [
            "ADD_FILE",
            "ADD_SUBDIR",
            "DELETE_CHILD",
            "WRITE_ATTR",
            "WRITE_EA",
        ]
        dir_ace["rights"].extend(rw_rights)
        file_ace["rights"].extend(rw_rights)

    return [dir_ace, file_ace]
