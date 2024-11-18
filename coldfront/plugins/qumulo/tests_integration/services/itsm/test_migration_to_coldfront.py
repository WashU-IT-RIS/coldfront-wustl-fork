import os

from django.test import TestCase, tag

from unittest import mock

from coldfront.plugins.qumulo.services.itsm.migrate_to_coldfront import (
    MigrateToColdfront,
)

from coldfront.core.test_helpers.factories import (
    AllocationAttributeTypeFactory,
    AllocationStatusChoiceFactory,
    AllocationUserStatusChoiceFactory,
    FieldOfScienceFactory,
    ProjectStatusChoiceFactory,
    ProjectUserRoleChoiceFactory,
    ProjectUserStatusChoiceFactory,
    ResourceFactory,
)

from coldfront.core.test_helpers.factories import field_of_science_provider


class TestMigrationToColdfront(TestCase):

    def setUp(self) -> None:
        self.migrate = MigrateToColdfront()
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
            "funding_number",
            "secure",
            "audit",
            "billing_startdate",
            "sponsor_department_number",
            "fileset_name",
            "fileset_alias",
            "exempt",
            "comment",
            "billing_cycle",
            "subsidized",
            "allow_nonfaculty",
            "sla",
        ]
        for allocation_attribute_name in allocation_attribute_names:
            AllocationAttributeTypeFactory(name=allocation_attribute_name)

        ResourceFactory(name="Storage2")
        ResourceFactory(name="rw")
        ResourceFactory(name="ro")

    @tag("integration")
    def test_migrate_to_coldfront_by_fileset_name(self):
        self.migrate.by_fileset_name("jin810_active")
        # fileset_key = "not_going_to_be_found"
        # self.assertRaises(
        #     Exception,
        #     self.migrate.by_fileset_name,
        #     fileset_key,
        #     msg=(f'ITSM allocation was not found for "{fileset_key}"'),
        # )

    @tag("integration")
    def test_migrate_to_coldfront_by_fileset_alias(self):
        # self.migrate.by_fileset_alias("jin810_active")
        # fileset_key = "not_going_to_be_found"
        # self.assertRaises(
        #    Exception,
        #    self.migrate.by_fileset_alias,
        #    fileset_key,
        #   msg=(f'ITSM allocation was not found for "{fileset_key}"'),
        # )
        pass
