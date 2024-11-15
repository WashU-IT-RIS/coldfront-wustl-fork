import os

from django.test import TestCase, tag

from unittest import mock

from coldfront.plugins.qumulo.services.itsm.migrate_to_coldfront import (
    MigrateToColdfront,
)

from coldfront.core.test_helpers.factories import field_of_science_provider

from faker import Faker


class TestMigrationToColdfront(TestCase):

    def setUp(self) -> None:
        self.migrate = MigrateToColdfront()
        field_of_science_provider.add_element("Other")

    @tag("integration")
    def test_migrate_to_coldfront_by_fileset_name(self):
        self.migrate.by_fileset_name("jin810_active")
        fileset_key = "not_going_to_be_found"
        self.assertRaises(
            Exception,
            self.migrate.by_fileset_name,
            fileset_key,
            msg=(f'ITSM allocation was not found for "{fileset_key}"'),
        )

    @tag("integration")
    def test_migrate_to_coldfront_by_fileset_alias(self):
        self.migrate.by_fileset_alias("jin810_active")
        fileset_key = "not_going_to_be_found"
        self.assertRaises(
            Exception,
            self.migrate.by_fileset_alias,
            fileset_key,
            msg=(f'ITSM allocation was not found for "{fileset_key}"'),
        )
