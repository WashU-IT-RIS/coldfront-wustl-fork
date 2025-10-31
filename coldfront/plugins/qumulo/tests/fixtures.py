from typing import Any, Callable, Tuple, Union

from coldfront.core.allocation.models import Allocation
from coldfront.core.project.models import Project, ProjectAttributeType
from coldfront.core.test_helpers.factories import (
    AAttributeTypeFactory,
    AllocationAttributeFactory,
    AllocationAttributeTypeFactory,
    AllocationStatusChoiceFactory,
    AllocationUserStatusChoiceFactory,
    FieldOfScienceFactory,
    ProjectAttributeFactory,
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
    Storage3Factory,
)


def create_metadata_for_testing() -> None:
    create_attribute_types_for_ris_allocations()
    create_project_choices()
    create_allocation_choices()
    create_ris_resources()


def create_ris_project_and_allocations_storage2(
    storage_filesystem_path: str,
    pi_username: str = None,
    **kwargs: dict[str, Any],
) -> Tuple[Project, dict[str, Allocation]]:
    return __create_ris_project_and_allocations(
        Storage2Factory, storage_filesystem_path, pi_username=pi_username, **kwargs
    )


def create_ris_project_and_allocations_storage3(
    storage_filesystem_path: str,
    pi_username: str = None,
    **kwargs: dict[str, Any],
) -> Tuple[Project, dict[str, Allocation]]:
    return __create_ris_project_and_allocations(
        Storage3Factory, storage_filesystem_path, pi_username=pi_username, **kwargs
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
        name="Storage3",
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


def __create_ris_project_and_allocations(
    storage_factory: Callable[[], Union[Storage2Factory, Storage3Factory]],
    storage_filesystem_path: str,
    pi_username: str = None,
    **kwargs: dict[str, Any],
) -> Tuple[Project, dict[str, Allocation]]:
    pi = UserFactory(username=pi_username) if pi_username else UserFactory()
    project = RisProjectFactory(pi=pi)
    ProjectUserFactory(
        project=project,
        user=project.pi,
        role=ProjectUserRoleChoiceFactory(name="Manager"),
        status=ProjectUserStatusChoiceFactory(name="New"),
    )

    # django_get_or_create was not implemented in the core, so get the desired object
    # TODO implement a RIS specific factory
    sponsor_department_number = ProjectAttributeType.objects.get(
        name="sponsor_department_number"
    )
    ProjectAttributeFactory(
        project=project,
        proj_attr_type=sponsor_department_number,
    )

    storage_allocation = storage_factory(project=project, **kwargs)

    kwargs_allocation_attributes = {
        "billing_contact": project.pi.email,
        **kwargs,
    }
    _create_allocations_attribute_for_storage_allocation(
        storage_allocation, storage_filesystem_path, **kwargs_allocation_attributes
    )

    AllocationUserFactory(
        allocation=storage_allocation,
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
        {
            "storage_allocation": storage_allocation,
            "rw_allocation": rw_group,
            "ro_allocation": ro_group,
        },
    )


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
        ("service_rate_category", "Text"),
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


def _create_allocations_attribute_for_storage_allocation(
    storage_allocation: Allocation,
    storage_filesystem_path: str,
    **kwargs: dict[str, Any],
) -> None:
    # TODO refactor to use a dataclass or similar for options
    storage_allocation_attribute_names = [
        ("storage_name", kwargs.get("storage_name", "Text")),
        ("storage_ticket", kwargs.get("storage_ticket", "ITSD-22222")),
        ("storage_quota", kwargs.get("storage_quota", 5)),
        ("storage_protocols", kwargs.get("storage_protocols", "SMB")),
        ("storage_filesystem_path", storage_filesystem_path),
        ("storage_export_path", storage_filesystem_path),
        ("cost_center", kwargs.get("cost_center", "COST-12345")),
        ("department_number", kwargs.get("department_number", "Dept-67890")),
        ("billing_contact", kwargs.get("billing_contact", "")),
        ("service_rate_category", kwargs.get("service_rate_category", "consumption")),
        ("secure", kwargs.get("secure", "Yes")),
        ("audit", kwargs.get("audit", "Yes/No")),
        ("billing_startdate", kwargs.get("billing_startdate", "Date")),
        ("sponsor_department_number", kwargs.get("sponsor_department_number", "Text")),
        ("billing_exempt", kwargs.get("billing_exempt", "No")),
        ("billing_cycle", kwargs.get("billing_cycle", "monthly")),
        ("subsidized", kwargs.get("subsidized", "No")),
    ]

    for attribute_name, value in storage_allocation_attribute_names:
        allocation_attribute_type = AllocationAttributeTypeFactory(name=attribute_name)
        AllocationAttributeFactory(
            allocation=storage_allocation,
            allocation_attribute_type=allocation_attribute_type,
            value=value,
        )
