from typing import Tuple

import factory
from coldfront.core.allocation.models import Allocation
from coldfront.core.project.models import Project
from coldfront.core.test_helpers.factories import (
    AAttributeTypeFactory,
    AllocationAttributeFactory,
    AllocationAttributeTypeFactory,
    AllocationStatusChoiceFactory,
    AllocationUserStatusChoiceFactory,
    FieldOfScienceFactory,
    ProjectAttributeTypeFactory,
    ProjectStatusChoiceFactory,
    ProjectUserFactory,
    ProjectUserRoleChoiceFactory,
    ProjectUserStatusChoiceFactory,
    PAttributeTypeFactory,
    ResourceFactory,
    ResourceTypeFactory,
    AllocationUserFactory,
    UserFactory,
)

from coldfront.core.test_helpers.factories import field_of_science_provider
from coldfront.plugins.qumulo.tests.helper_classes.factories import (
    RisProjectFactory,
    ReadOnlyGroupFactory,
    ReadWriteGroupFactory,
    Storage2Factory,
)


def create_metadata_for_testing() -> None:
    create_attribute_types_for_ris_allocations()
    create_project_choices()
    create_allocation_choices()
    create_ris_resources()


def create_ris_project_and_allocations(
    path: str = None,
) -> Tuple[Project, list[Allocation]]:
    project = RisProjectFactory()

    ProjectUserFactory(
        project=project,
        user=project.pi,
        role=ProjectUserRoleChoiceFactory(name="Manager"),
        status=ProjectUserStatusChoiceFactory(name="New"),
    )

    storage2 = Storage2Factory(project=project)
    AllocationUserFactory(
        allocation=storage2,
        user=project.pi,
        status=AllocationUserStatusChoiceFactory(name="Active"),
    )

    rw_group = ReadWriteGroupFactory(project=project)
    AllocationUserFactory.create_batch(
        2,
        allocation=rw_group,
        status=AllocationUserStatusChoiceFactory(name="Active"),
    )

    ro_group = ReadOnlyGroupFactory(project=project)
    AllocationUserFactory(
        allocation=ro_group,
        status=AllocationUserStatusChoiceFactory(name="Active"),
    )
    return (
        project,
        [storage2, rw_group, ro_group],
    )


def create_project_choices() -> None:
    ProjectStatusChoiceFactory(name="New")
    ProjectUserRoleChoiceFactory(name="Manager")
    ProjectUserStatusChoiceFactory(name="Active")


def create_allocation_choices() -> None:
    FieldOfScienceFactory(description="Other")
    AllocationStatusChoiceFactory(name="Pending")
    AllocationStatusChoiceFactory(name="Active")
    AllocationUserStatusChoiceFactory(name="Active")


def create_ris_resources() -> None:
    ResourceFactory(
        name="Storage2",
        resource_type=ResourceTypeFactory(name="Storage"),
        description="Storage allocation via Qumulo",
    )
    ResourceFactory(
        name="rw", resource_type=ResourceTypeFactory(name="ACL"), description="RW ACL"
    )
    ResourceFactory(
        name="ro", resource_type=ResourceTypeFactory(name="ACL"), description="RO ACL"
    )


def create_attribute_types_for_ris_allocations() -> None:
    _add_field_of_science_options_to_provider(["Other"])
    _create_acl_allocation_attribute_names()
    _create_storage_allocation_attribute_types()
    _create_project_attribute_types()


def _create_storage_allocation_attribute_types() -> None:

    storage_allocation_attribute_names = [
        ("storage_name", "Text"),
        ("storage_ticket", "Text"),
        ("storage_quota", "Int"),
        ("storage_protocols", "Text"),
        ("storage_filesystem_path", "Text"),
        ("storage_export_path", "Text"),
        ("cost_center", "Text"),
        ("department_number", "Text"),
        ("technical_contact", "Text"),
        ("billing_contact", "Text"),
        ("service_rate", "Text"),
        ("storage_acl_name", "Text"),
        ("storage_allocation_pk", "Int"),
        ("secure", "Yes/No"),
        ("audit", "Yes/No"),
        ("billing_startdate", "Date"),
        ("sponsor_department_number", "Text"),
        ("fileset_name", "Text"),
        ("fileset_alias", "Text"),
        ("billing_exempt", "Yes/No"),
        ("itsm_comment", "JSON"),
        ("billing_cycle", "Text"),
        ("subsidized", "Yes/No"),
        ("allow_nonfaculty", "Yes/No"),
        ("sla_name", "Text"),
        ("prepaid_time", "Int"),
        ("prepaid_billing_date", "Date"),
    ]
    _create_allocation_attribute_types(storage_allocation_attribute_names)


def _create_acl_allocation_attribute_names() -> None:
    acl_allocation_attribute_names = [
        ("storage_acl_name", "Text"),
        ("storage_allocation_pk", "Int"),
    ]
    _create_allocation_attribute_types(acl_allocation_attribute_names)


def _create_project_attribute_types() -> None:
    project_attribute_names = [
        ("is_condo_group", "Yes/No"),
        ("sponsor_department_number", "Text"),
        ("allow_nonfaculty", "Yes/No"),
    ]
    for project_attribute_name, project_attribute_type in project_attribute_names:
        ProjectAttributeTypeFactory(
            name=project_attribute_name,
            attribute_type=PAttributeTypeFactory(name=project_attribute_type),
        )


def _add_field_of_science_options_to_provider(options: list) -> None:
    for option in options:
        field_of_science_provider.add_element(option)


def _create_allocation_attribute_types(attribute_types: list[Tuple[str, str]]) -> None:
    for (
        allocation_attribute_name,
        allocation_attribute_type,
    ) in attribute_types:

        AllocationAttributeTypeFactory(
            name=allocation_attribute_name,
            attribute_type=AAttributeTypeFactory(name=allocation_attribute_type),
        )
