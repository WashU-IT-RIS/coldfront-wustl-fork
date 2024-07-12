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

from coldfront_plugin_qumulo.utils.acl_allocations import AclAllocations
from coldfront_plugin_qumulo.management.commands.qumulo_plugin_setup import (
    call_base_commands,
)

import json

from django.core.management import call_command


def build_models() -> dict["project":Project, "user":User]:
    call_command("import_field_of_science_data")
    call_command("add_default_project_choices")
    call_command("add_resource_defaults")
    call_command("add_allocation_defaults")
    call_base_commands()

    # create user
    user = User.objects.create(
        id=1, username="test", password="test", email="test@wustl.edu"
    )

    # create project
    activeStatus = ProjectStatusChoice.objects.get(name="Active")
    fieldOfScience = FieldOfScience.objects.get(description="Other")
    project = Project.objects.create(
        id=1,
        title="Project 1",
        pi=user,
        status=activeStatus,
        field_of_science=fieldOfScience,
    )

    return {"project": project, "user": user}


def create_allocation(project: Project, user: User, form_data: dict):
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

    set_allocation_attributes(form_data, allocation)

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


def set_allocation_attributes(form_data: dict, allocation):
    allocation_attribute_names = [
        "storage_name",
        "storage_quota",
        "storage_protocols",
        "storage_filesystem_path",
        "storage_export_path",
    ]

    for allocation_attribute_name in allocation_attribute_names:
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
