from datetime import datetime, timezone
from typing import Any, Callable, Tuple, Type, Union

import factory

from coldfront.core.allocation.models import Allocation, AllocationAttribute
from coldfront.core.project.models import Project, ProjectAttributeType
from coldfront.core.test_helpers.factories import (
    AAttributeTypeFactory,
    AllocationAttributeFactory,
    AllocationAttributeTypeFactory,
    AllocationStatusChoiceFactory,
    AllocationUserStatusChoiceFactory,
    AllocationLinkageFactory,
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

storage_factory_type = Callable[[], Union[Storage2Factory, Storage3Factory]]


def create_metadata_for_testing() -> None:
    create_attribute_types_for_ris_allocations()
    create_project_choices()
    create_allocation_choices()
    create_ris_resources()


def create_ris_project_and_allocations_storage2(
    storage_filesystem_path: str,
    pi_username: str = None,
    **kwargs: dict[str, Any],
) -> dict[Project, dict[str, Allocation]]:
    return __create_ris_project_and_allocations(
        Storage2Factory, storage_filesystem_path, pi_username=pi_username, **kwargs
    )


def create_ris_project_and_allocations_storage3(
    storage_filesystem_path: str,
    pi_username: str = None,
    **kwargs: dict[str, Any],
) -> dict[Project, dict[str, Allocation]]:
    return __create_ris_project_and_allocations(
        Storage3Factory, storage_filesystem_path, pi_username=pi_username, **kwargs
    )


def create_ris_project(pi_username: str = None) -> Project:
    return __create_ris_project(pi_username=pi_username)


def create_allocation_with_allocation_attributes(
    storage_factory: storage_factory_type,
    storage_filesystem_path: str,
    project: Project = None,
    **kwargs: dict[str, Any],
) -> None:
    if not project:
        project = __create_ris_project()

    storage_allocation = storage_factory(project=project, **kwargs)

    kwargs_allocation_attributes = {
        "billing_contact": project.pi.email,
        "storage_name": project.pi.username,
        **kwargs,
    }
    create_allocations_attribute_for_storage_allocation(
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

    return {
        "allocations": {
            "storage_allocation": storage_allocation,
            "rw_group": rw_group,
            "ro_group": ro_group,
        }
    }


def create_project_choices() -> None:
    ProjectStatusChoiceFactory(name="New")
    ProjectUserRoleChoiceFactory(name="Manager")
    ProjectUserStatusChoiceFactory(name="Active")


def create_allocation_choices() -> None:
    FieldOfScienceFactory(description="Other")
    AllocationUserStatusChoiceFactory(name="Active")
    AllocationStatusChoiceFactory(name="Pending")
    AllocationStatusChoiceFactory(name="Active")
    AllocationStatusChoiceFactory(name="New")
    AllocationStatusChoiceFactory(name="Deleted")
    AllocationStatusChoiceFactory(name="Ready for deletion")
    AllocationStatusChoiceFactory(name="Invalid")


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


def __create_ris_project(pi_username: str = None, **kwargs: dict[str, Any]) -> Project:
    pi = UserFactory(username=pi_username) if pi_username else UserFactory()
    project = RisProjectFactory(pi=pi, **kwargs)
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
    return project


def __create_ris_project_and_allocations(
    storage_factory: storage_factory_type,
    storage_filesystem_path: str,
    pi_username: str = None,
    **kwargs: dict[str, Any],
) -> dict[str, Union[Project, dict[str, Allocation]]]:
    project: Project = __create_ris_project(pi_username=pi_username)

    allocations: dict[str, Allocation] = create_allocation_with_allocation_attributes(
        storage_factory=storage_factory,
        storage_filesystem_path=storage_filesystem_path,
        project=project,
        **kwargs,
    )

    return {"project": project} | allocations


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


def create_allocations_attribute_for_storage_allocation(
    storage_allocation: Allocation,
    storage_filesystem_path: str,
    **kwargs: dict[str, Any],
) -> None:
    # TODO refactor to use a dataclass or similar for options
    billing_startdate = factory.fuzzy.FuzzyDateTime(start_dt=datetime.now(timezone.utc))
    storage_allocation_attribute_names = [
        ("storage_name", kwargs.get("storage_name")),
        (
            "storage_ticket",
            kwargs.get("storage_ticket", factory.Sequence(lambda n: f"ITSD-{n}")),
        ),
        ("storage_quota", kwargs.get("storage_quota", 5)),
        ("storage_protocols", kwargs.get("storage_protocols", "SMB")),
        ("storage_filesystem_path", storage_filesystem_path),
        ("storage_export_path", storage_filesystem_path),
        (
            "cost_center",
            kwargs.get("cost_center", factory.Sequence(lambda n: f"COST-{n}")),
        ),
        (
            "department_number",
            kwargs.get("department_number", factory.Sequence(lambda n: f"Dept-{n}")),
        ),
        ("billing_contact", kwargs.get("billing_contact", "")),
        ("service_rate_category", kwargs.get("service_rate_category", "consumption")),
        ("secure", kwargs.get("secure", "Yes")),
        ("audit", kwargs.get("audit", "Yes")),
        ("billing_startdate", kwargs.get("billing_startdate", billing_startdate)),
        (
            "sponsor_department_number",
            kwargs.get(
                "sponsor_department_number", factory.Sequence(lambda n: f"Dept-{n}")
            ),
        ),
        ("billing_exempt", kwargs.get("billing_exempt", "No")),
        ("billing_cycle", kwargs.get("billing_cycle", "monthly")),
        ("subsidized", kwargs.get("subsidized", "No")),
    ]

    for attribute_name, value in storage_allocation_attribute_names:
        create_allocation_attribute(
            allocation=storage_allocation,
            attribute_name=attribute_name,
            value=value,
        )


def create_allocation_attribute(
    allocation: Allocation,
    attribute_name: str,
    value: Any,
) -> AllocationAttribute:
    allocation_attribute_type = AllocationAttributeTypeFactory(name=attribute_name)

    return AllocationAttributeFactory(
        allocation=allocation,
        allocation_attribute_type=allocation_attribute_type,
        value=value,
    )


def create_allocation_linkage(
    parent: Allocation,
    children: list[Allocation],
) -> AllocationLinkageFactory:
    linkage = AllocationLinkageFactory(parent=parent, children=children)
    return linkage


def create_sub_allocation(
    parent: Allocation,
    **kwargs: dict[str, Any],
) -> Allocation:
    project: Project = parent.project
    status = parent.status
    storage_resource = parent.resources.get(resource_type__name="Storage")
    if storage_resource.name == "Storage2":
        sub_allocation: Allocation = Storage2Factory(
            project=project, status=status, **kwargs
        )
    elif storage_resource.name == "Storage3":
        sub_allocation: Allocation = Storage3Factory(
            project=project, status=status, **kwargs
        )
    else:
        raise ValueError(
            f"Unsupported resource type for parent allocation: {parent.resources}"
        )
    create_allocation_linkage(parent, [sub_allocation])
    return sub_allocation
