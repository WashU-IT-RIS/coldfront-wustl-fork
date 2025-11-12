from django.test import TestCase, tag

from coldfront.plugins.qumulo.services.itsm.migrate_to_coldfront import (
    MigrateToColdfront,
)

from coldfront.plugins.qumulo.tests.fixtures import (
    create_metadata_for_testing,
)


class TestMigrateToColdfront(TestCase):

    def setUp(self) -> None:
        self.migrate = MigrateToColdfront()
        create_metadata_for_testing()

    @tag("integration")
    def test_migrate_to_coldfront_by_fileset_name_found(self):
        raised = False
        try:
            self.migrate.by_fileset_name("kchoi_active", "Storage2")
        except Exception:
            raised = True
        self.assertFalse(raised)

    @tag("integration")
    def test_migrate_to_coldfront_by_fileset_name_not_found(self):
        fileset_key = "not_going_to_be_found"
        self.assertRaises(
            Exception,
            self.migrate.by_fileset_name,
            fileset_key,
            msg=(f'ITSM allocation was not found for "{fileset_key}"'),
        )

    @tag("integration")
    def test_migrate_to_coldfront_by_storage_provision_name_found(self):
        raised = False
        try:
            self.migrate.by_storage_provision_name("/vol/rdcw-fs1/kchoi", "Storage2")
        except Exception:
            raised = True
        self.assertFalse(raised)

    @tag("integration")
    def test_migrate_to_coldfront_by_by_storage_provision_name_not_found(self):
        fileset_key = "not_going_to_be_found"
        self.assertRaises(
            Exception,
            self.migrate.by_storage_provision_name,
            fileset_key,
            msg=(f'ITSM allocation was not found for "{fileset_key}"'),
        )
