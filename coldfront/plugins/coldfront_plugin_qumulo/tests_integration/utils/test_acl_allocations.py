from django.test import TestCase
from unittest.mock import MagicMock, patch

from coldfront_plugin_qumulo.utils.acl_allocations import AclAllocations
from coldfront_plugin_qumulo.views.allocation_view import AllocationView

from coldfront.core.user.models import User
from coldfront.core.project.models import Project
from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttributeType,
    AllocationAttribute,
)

from coldfront_plugin_qumulo.utils.qumulo_api import QumuloAPI
from coldfront_plugin_qumulo.utils.active_directory_api import ActiveDirectoryAPI
from coldfront_plugin_qumulo.tests.utils.mock_data import build_models

import time


class TestAclAllocations(TestCase):
    def setUp(self) -> None:
        model_data = build_models()

        self.user: User = model_data["user"]
        self.project: Project = model_data["project"]

        self.ad_api = ActiveDirectoryAPI()
        self.test_wustlkey = "test"
        self.user_in_group_filter = (
            lambda group_name: f"(&(objectClass=user)(sAMAccountName={self.test_wustlkey})(memberof=CN={group_name},OU=QA,OU=RIS,OU=Groups,DC=accounts,DC=ad,DC=wustl,DC=edu))"
        )

        return super().setUp()

    def test_create_acl_allocation(self):
        acl_type = "ro"
        test_users = ["test"]

        acl_allocations = AclAllocations(project_pk=self.project)
        acl_allocations.create_acl_allocation(acl_type=acl_type, users=test_users)

        all_allocation_objects = Allocation.objects.all()
        allocation = all_allocation_objects[0]

        group_name = "storage-test-ro"

        self.ad_api.conn.search(
            "dc=accounts,dc=ad,dc=wustl,dc=edu",
            f"(cn={group_name})",
        )
        group_dn = self.ad_api.conn.response[0]["dn"]
        response_group_dn = self.ad_api.get_group_dn(group_name)

        self.assertEqual(response_group_dn, group_dn)

        self.ad_api.delete_ad_group(group_name)

        Allocation.delete(allocation)
        self.assertEqual(len(Allocation.objects.all()), 0)

    def test_set_qumulo_acls_on_root(self):
        qumulo_api = QumuloAPI()

        # including a timestamp to test response on brand new AD group creation
        name_base = "test-set-qumulo-acls-{}-del-me".format(str(int(time.time())))

        form_data = {
            "storage_name": name_base,
            "storage_quota": 15,
            "storage_protocols": ["nfs"],
            "storage_filesystem_path": "/" + name_base,
            "storage_export_path": "/" + name_base,
            "rw_users": ["harterj"],
            "ro_users": ["gunnar"],
            "project_pk": self.project.pk,
        }

        allocation_data = AllocationView.create_new_allocation(form_data, self.user)

        qumulo_api.create_allocation(
            form_data["storage_protocols"],
            form_data["storage_export_path"],
            form_data["storage_filesystem_path"],
            form_data["storage_name"],
            20000000000,
        )

        try:
            AclAllocations.set_qumulo_acls(allocation_data["allocation"], qumulo_api)
        except Exception as e:
            print("excepted")
            print(e)

        acls = qumulo_api.rc.fs.get_acl_v2(form_data["storage_filesystem_path"])

        self.assertIn("aces", acls)

        found_valid_ace = False
        for ace in acls["aces"]:
            if ace["trustee"]["name"] == "ACCOUNTS\\storage-{}-ro".format(
                form_data["storage_name"]
            ):
                found_valid_ace = True

        clear_acl(form_data["storage_filesystem_path"], qumulo_api)

        qumulo_api._delete_allocation(
            form_data["storage_protocols"],
            form_data["storage_filesystem_path"],
            form_data["storage_export_path"],
            form_data["storage_name"],
        )

        for access_allocation in allocation_data["access_allocations"]:
            self.ad_api.delete_ad_group(
                access_allocation.get_attribute(name="storage_acl_name")
            )

        self.assertTrue(found_valid_ace)


def clear_acl(path: str, qumulo_api: QumuloAPI):
    acl = {"control": ["PRESENT"], "posix_special_permissions": [], "aces": []}

    return qumulo_api.rc.fs.set_acl_v2(acl=acl, path=path)


def set_allocation_attributes(form_data: dict, allocation):
    allocation_attribute_names = [
        "storage_name",
        "storage_quota",
        "storage_protocols",
        "storage_filesystem_path",
        "storage_export_path",
        "cost_center",
        "department_number",
        "storage_ticket",
        "technical_contact",
        "billing_contact",
        "service_rate",
    ]

    for allocation_attribute_name in allocation_attribute_names:
        allocation_attribute_type = AllocationAttributeType.objects.get(
            name=allocation_attribute_name
        )

        AllocationAttribute.objects.create(
            allocation_attribute_type=allocation_attribute_type,
            allocation=allocation,
            value=form_data.get(allocation_attribute_name),
        )
