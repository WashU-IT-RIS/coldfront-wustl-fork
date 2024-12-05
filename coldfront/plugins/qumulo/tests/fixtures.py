
from coldfront.core.test_helpers.factories import (
    AllocationAttributeTypeFactory,
    AllocationStatusChoiceFactory,
    AllocationUserStatusChoiceFactory,
    FieldOfScienceFactory,
    ProjectAttributeTypeFactory,
    ProjectStatusChoiceFactory,
    ProjectUserRoleChoiceFactory,
    ProjectUserStatusChoiceFactory,
    PAttributeTypeFactory,
    ResourceFactory,
)

from coldfront.core.test_helpers.factories import field_of_science_provider

def create_allocation_assets() -> None:
    field_of_science_provider.add_element("Other")
    FieldOfScienceFactory(description="Other")
    ProjectStatusChoiceFactory(name="New")
    ProjectUserRoleChoiceFactory(name="Manager")
    ProjectUserStatusChoiceFactory(name="Active")
    AllocationStatusChoiceFactory(name="Pending")
    AllocationUserStatusChoiceFactory(name="Active")
    allocation_attribute_names = [
        "storage_name",
        "storage_ticket",
        "storage_quota",
        "storage_protocols",
        "storage_filesystem_path",
        "storage_export_path",
        "cost_center",
        "department_number",
        "technical_contact",
        "billing_contact",
        "service_rate",
        "storage_acl_name",
        "storage_allocation_pk",
        "secure",
        "audit",
        "billing_startdate",
        "sponsor_department_number",
        "fileset_name",
        "fileset_alias",
        "exempt",
        "itsm_comment",
        "billing_cycle",
        "subsidized",
        "allow_nonfaculty",
        "sla_name",
    ]
    for allocation_attribute_name in allocation_attribute_names:
        AllocationAttributeTypeFactory(name=allocation_attribute_name)

    project_attribute_names = [
        "is_condo_group",
        "sponsor_department_number",
        "allow_nonfaculty",
    ]
    for project_attribute_name in project_attribute_names:
        ProjectAttributeTypeFactory(
            name=project_attribute_name,
            attribute_type=PAttributeTypeFactory(name="Text"),
        )

    ResourceFactory(name="Storage2")
    ResourceFactory(name="rw")
    ResourceFactory(name="ro")
