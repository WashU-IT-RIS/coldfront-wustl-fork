from coldfront.core.user.models import User
from coldfront.core.field_of_science.models import FieldOfScience
from coldfront.core.project.models import Project, ProjectStatusChoice
from coldfront.core.resource.models import Resource
from coldfront.core.allocation.models import (
    AllocationStatusChoice,
    AllocationAttributeType,
    AllocationUserStatusChoice,
    AllocationUser,
    Allocation,
    AllocationAttribute,
)

from coldfront.core.allocation.models import AllocationLinkage

from coldfront.plugins.qumulo.utils.acl_allocations import AclAllocations
from coldfront.plugins.qumulo.management.commands.qumulo_plugin_setup import (
    call_base_commands,
)

import json

from django.core.management import call_command

from typing import Optional

default_form_data = {
    "storage_filesystem_path": "foo",
    "storage_export_path": "bar",
    "storage_ticket": "ITSD-54321",
    "storage_name": "baz",
    "storage_quota": 7,
    "protocols": ["nfs"],
    "rw_users": ["test"],
    "ro_users": ["test1"],
    "cost_center": "Uncle Pennybags",
    "department_number": "Time Travel Services",
    "service_rate": "general",
}


def build_models() -> dict["project":Project, "user":User]:
    build_models_without_project()

    return build_user_plus_project("test", "Project 1")


def build_models_without_project() -> None:
    call_command("import_field_of_science_data")
    call_command("add_default_project_choices")
    call_command("add_resource_defaults")
    call_command("add_allocation_defaults")
    call_base_commands()


def build_user_plus_project(
    username: str, project_name: str
) -> dict["project":Project, "user":User]:
    prev_users = list(User.objects.all())
    max_id = 0
    if prev_users:
        for prev_user in prev_users:
            if prev_user.id > max_id:
                max_id = prev_user.id
    max_id = max_id + 1
    user_id = max_id

    user = User.objects.create(
        id=user_id, username=username, password="test", email=f"{username}@wustl.edu"
    )

    activeStatus = ProjectStatusChoice.objects.get(name="Active")
    fieldOfScience = FieldOfScience.objects.get(description="Other")

    prev_projects = list(Project.objects.all())

    max_id = 0
    if prev_projects:
        for prev_project in prev_projects:
            if prev_project.id > max_id:
                max_id = prev_project.id
    max_id = max_id + 1
    project_id = max_id

    project = Project.objects.create(
        id=project_id,
        title=project_name,
        pi=user,
        status=activeStatus,
        field_of_science=fieldOfScience,
    )

    return {"project": project, "user": user}


def create_allocation(
    project: Project, user: User, form_data: dict, parent: Optional[Allocation] = None
):
    allocation = Allocation.objects.create(
        project=project,
        justification="",
        quantity=1,
        status=AllocationStatusChoice.objects.get(name="Pending"),
    )

    active_status = AllocationUserStatusChoice.objects.get(name="Active")
    AllocationUser.objects.create(
        allocation=allocation, user=user, status=active_status
    )

    resource = Resource.objects.get(name="Storage2")
    allocation.resources.add(resource)

    set_allocation_attributes(form_data, allocation, parent)

    create_access_privileges(form_data, project, allocation)

    return allocation


def create_access_privileges(
    form_data: dict, project: Project, storage_allocation: Allocation
):
    rw_users = {
        "name": "RW Users",
        "resource": "rw",
        "users": form_data["rw_users"],
    }
    ro_users = {
        "name": "RO Users",
        "resource": "ro",
        "users": form_data["ro_users"],
    }

    for value in [rw_users, ro_users]:
        access_allocation = create_access_allocation(
            value, project, form_data["storage_name"], storage_allocation
        )

        for username in value["users"]:
            AclAllocations.add_user_to_access_allocation(username, access_allocation)


def create_access_allocation(
    access_data: dict,
    project: Project,
    storage_name: str,
    storage_allocation: Allocation,
):
    access_allocation = Allocation.objects.create(
        project=project,
        justification=access_data["name"],
        quantity=1,
        status=AllocationStatusChoice.objects.get(name="Active"),
    )

    storage_acl_name_attribute = AllocationAttributeType.objects.get(
        name="storage_acl_name"
    )
    AllocationAttribute.objects.create(
        allocation_attribute_type=storage_acl_name_attribute,
        allocation=access_allocation,
        value="storage-{0}-{1}".format(storage_name, access_data["resource"]),
    )

    storage_allocation_pk_attribute = AllocationAttributeType.objects.get(
        name="storage_allocation_pk"
    )
    AllocationAttribute.objects.create(
        allocation_attribute_type=storage_allocation_pk_attribute,
        allocation=access_allocation,
        value=storage_allocation.pk,
    )

    resource = Resource.objects.get(name=access_data["resource"])
    access_allocation.resources.add(resource)

    return access_allocation


def set_allocation_attributes(
    form_data: dict, allocation: Allocation, parent: Optional[Allocation] = None
):
    if parent:
        linkage, _ = AllocationLinkage.objects.get_or_create(parent=parent)
        linkage.children.add(allocation)
        linkage.save()

    allocation_attribute_names = [
        "storage_name",
        "storage_quota",
        "storage_protocols",
        "storage_filesystem_path",
        "storage_export_path",
        "department_number",
        "cost_center",
        "service_rate",
        "storage_ticket",
        "technical_contact",
        "billing_contact",
    ]

    for allocation_attribute_name in allocation_attribute_names:

        key = (
            allocation_attribute_name
            if allocation_attribute_name != "storage_protocols"
            else "protocols"
        )
        if key not in form_data.keys():
            continue

        allocation_attribute_type = AllocationAttributeType.objects.get(
            name=allocation_attribute_name
        )

        if allocation_attribute_name == "storage_protocols":
            protocols = form_data.get("protocols")

            AllocationAttribute.objects.create(
                allocation_attribute_type=allocation_attribute_type,
                allocation=allocation,
                value=json.dumps(protocols),
            )
        else:
            AllocationAttribute.objects.create(
                allocation_attribute_type=allocation_attribute_type,
                allocation=allocation,
                value=form_data.get(allocation_attribute_name),
            )


mock_quotas = {
    "quotas": [
        {
            "id": "111111111",
            "path": "/storage2/fs1/not_found_in_coldfront/",
            "limit": "20000000000000",
            "capacity_usage": "1",
        },
        {
            "id": "18600003",
            "path": "/storage2/fs1/sleong/",
            "limit": "100000000000000",
            "capacity_usage": "37089736126464",
        },
        {
            "id": "34717218",
            "path": "/storage2/fs1/prewitt_test/",
            "limit": "1099511627776",
            "capacity_usage": "53248",
        },
        {
            "id": "36270003",
            "path": "/storage2/fs1/tychele_test/",
            "limit": "109951162777600",
            "capacity_usage": "57344",
        },
        {
            "id": "36290003",
            "path": "/storage2/fs1/tychele_test/Active/tychele_suballoc_test/",
            "limit": "109951162777600",
            "capacity_usage": "4096",
        },
        {
            "id": "36850003",
            "path": "/storage2/fs1/prewitt_test/Active/prewitt_test_2_a/",
            "limit": "1099511627776",
            "capacity_usage": "4096",
        },
        {
            "id": "36860003",
            "path": "/storage2/fs1/prewitt_test_2/",
            "limit": "1099511627776",
            "capacity_usage": "16384",
        },
        {
            "id": "37000005",
            "path": "/storage2/fs1/jian_test/",
            "limit": "10995116277760",
            "capacity_usage": "16384",
        },
        {
            "id": "38760894",
            "path": "/storage2/fs1/hong.chen_test/",
            "limit": "5497558138880",
            "capacity_usage": "40960",
        },
        {
            "id": "38760895",
            "path": "/storage2/fs1/i2_test/",
            "limit": "109951162777600",
            "capacity_usage": "20480",
        },
        {
            "id": "39720243",
            "path": "/storage2/fs1/swamidass_test/",
            "limit": "24189255811072",
            "capacity_usage": "16384",
        },
        {
            "id": "39720382",
            "path": "/storage2/fs1/prewitt_test_3/",
            "limit": "5497558138880",
            "capacity_usage": "16384",
        },
        {
            "id": "42020003",
            "path": "/storage2/fs1/hong.chen_test/Active/hong.chen_suballocation/",
            "limit": "5497558138880",
            "capacity_usage": "4096",
        },
        {
            "id": "42030003",
            "path": "/storage2/fs1/engineering_test/",
            "limit": "5497558138880",
            "capacity_usage": "307242479616",
        },
        {
            "id": "42030004",
            "path": "/storage2/fs1/sleong_summer/",
            "limit": "5497558138880",
            "capacity_usage": "713363001344",
        },
        {
            "id": "42050003",
            "path": "/storage2/fs1/wexler_test/",
            "limit": "5497558138880",
            "capacity_usage": "16384",
        },
        {
            "id": "42080003",
            "path": "/storage2/fs1/alex.holehouse_test/",
            "limit": "38482906972160",
            "capacity_usage": "16384",
        },
        {
            "id": "42080004",
            "path": "/storage2/fs1/wucci/",
            "limit": "5497558138880",
            "capacity_usage": "16384",
        },
        {
            "id": "42130003",
            "path": "/storage2/fs1/amlai/",
            "limit": "5497558138880",
            "capacity_usage": "4198400",
        },
        {
            "id": "43010004",
            "path": "/storage2/fs1/jin810_test/",
            "limit": "109951162777600",
            "capacity_usage": "16384",
        },
        {
            "id": "43010005",
            "path": "/storage2/fs1/dinglab_test/",
            "limit": "109951162777600",
            "capacity_usage": "16384",
        },
        {
            "id": "43050003",
            "path": "/storage2/fs1/wucci_test/",
            "limit": "109951162777600",
            "capacity_usage": "16384",
        },
        {
            "id": "43070003",
            "path": "/storage2/fs1/gtac-mgi_test2/",
            "limit": "5497558138880",
            "capacity_usage": "1477898227712",
        },
        {
            "id": "52929566",
            "path": "/storage2/fs1/mweil_test/",
            "limit": "5497558138880",
            "capacity_usage": "1436366471168",
        },
        {
            "id": "52929567",
            "path": "/storage2/fs1/amlai_test2/",
            "limit": "16492674416640",
            "capacity_usage": "997732352",
        },
        {
            "id": "52929568",
            "path": "/storage2/fs1/tychele_test2/",
            "limit": "109951162777600",
            "capacity_usage": "18083368955904",
        },
    ],
    "paging": {"next": ""},
}

quota_mock_allocation_data = {
    "/storage2/fs1/sleong/": {"limit": "100000000000000"},
    "/storage2/fs1/prewitt_test/": {"limit": "1099511627776"},
    "/storage2/fs1/tychele_test": {"limit": "109951162777600"},
    "/storage2/fs1/tychele_test/Active/tychele_suballoc_test": {
        "limit": "109951162777600"
    },
    "/storage2/fs1/prewitt_test/Active/prewitt_test_2_a": {"limit": "1099511627776"},
    "/storage2/fs1/prewitt_test_2": {"limit": "1099511627776"},
    "/storage2/fs1/jian_test": {"limit": "10995116277760"},
    "/storage2/fs1/hong.chen_test": {"limit": "5497558138880"},
    "/storage2/fs1/i2_test": {"limit": "109951162777600"},
    "/storage2/fs1/swamidass_test": {"limit": "24189255811072"},
    "/storage2/fs1/prewitt_test_3": {"limit": "5497558138880"},
    "/storage2/fs1/hong.chen_test/Active/hong.chen_suballocation": {
        "limit": "5497558138880"
    },
    "/storage2/fs1/engineering_test": {"limit": "5497558138880"},
    "/storage2/fs1/sleong_summer": {"limit": "5497558138880"},
    "/storage2/fs1/wexler_test": {"limit": "5497558138880"},
    "/storage2/fs1/alex.holehouse_test": {"limit": "38482906972160"},
    "/storage2/fs1/wucci": {"limit": "5497558138880"},
    "/storage2/fs1/amlai": {"limit": "5497558138880"},
    "/storage2/fs1/jin810_test": {"limit": "109951162777600"},
    "/storage2/fs1/dinglab_test": {"limit": "109951162777600"},
    "/storage2/fs1/wucci_test": {"limit": "109951162777600"},
    "/storage2/fs1/gtac-mgi_test2": {"limit": "5497558138880"},
    "/storage2/fs1/mweil_test": {"limit": "5497558138880"},
    "/storage2/fs1/amlai_test2": {"limit": "16492674416640"},
    "/storage2/fs1/tychele_test2": {"limit": "109951162777600"},
}
