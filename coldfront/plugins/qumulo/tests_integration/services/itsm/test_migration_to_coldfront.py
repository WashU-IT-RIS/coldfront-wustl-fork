import os

from django.test import TestCase, tag

from unittest import mock

from coldfront.plugins.qumulo.services.itsm.migrate_to_coldfront import (
    MigrateToColdfront,
)


class TestItsmClient(TestCase):

    def setUp(self) -> None:
        self.migrate = MigrateToColdfront()

    @tag("integration")
    def test_migrate_to_coldfront_by_fileset_name(self):
        self.migrate.by_fileset_name("jin810_active")
        self.migrate.by_fileset_name("not_going_to_be_found")

    @tag("integration")
    def test_migrate_to_coldfront_by_fileset_alias(self):
        itsm_client = self.itsm_client
        self.migrate.by_fileset_alias("jin810_active")
        self.migrate.by_fileset_alias("not_going_to_be_found")
