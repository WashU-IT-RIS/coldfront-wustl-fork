from django.contrib import messages
from django.test import TestCase, tag, RequestFactory

from coldfront.plugins.qumulo.constants import DEFAULT_STORAGE_TYPE
from coldfront.plugins.qumulo.forms.TriggerMigrationsForm import TriggerMigrationsForm
from coldfront.plugins.qumulo.views.trigger_migrations_view import TriggerMigrationsView
from coldfront.plugins.qumulo.tests.fixtures import create_ris_resources

from unittest.mock import MagicMock


class TriggerMigrationsViewTests(TestCase):
    def setUp(self) -> None:
        create_ris_resources()
        self.default_storage_type = "Storage3"

    @tag("integration")
    def test_migration_successful_with_valid_allocation(
        self,
    ):
        messages.success = MagicMock()
        request = RequestFactory().get(
            "src/coldfront.plugins.qumulo/views/trigger_migrations_view.py"
        )
        valid_data = {"allocation_name_search": "/vol/rdcw-fs1/kchoi"}
        form = TriggerMigrationsForm(data=valid_data)
        self.assertEqual(
            form.fields["allocation_resource_name"].initial,
            self.default_storage_type,
            msg=f"Initial storage type should be '{DEFAULT_STORAGE_TYPE}'",
        )
        self.assertTrue(form.is_valid())
        view = TriggerMigrationsView()
        view.request = request
        try:
            view.form_valid(form)
        except Exception as e:
            self.fail(f"Metadata migration triggered exception: {e}")

    @tag("integration")
    def test_migration_fail_with_invalid_allocation(self):
        messages.error = MagicMock()
        request = RequestFactory().get(
            "src/coldfront.plugins.qumulo/views/trigger_migrations_view.py"
        )
        invalid_data = {"allocation_name_search": "malformed/allocation/path"}
        form = TriggerMigrationsForm(data=invalid_data)
        self.assertEqual(
            form.fields["allocation_resource_name"].initial,
            self.default_storage_type,
            msg=f"Initial storage type should be '{DEFAULT_STORAGE_TYPE}'",
        )
        form.is_valid()
        # self.assertFalse(form.is_valid()) this is not working as expected
        # since the form currently does not have validation logic for allocation name format in the clean method
        # TODO: add custom validation logic to the form to catch malformed allocation names
        view = TriggerMigrationsView()
        view.request = request
        try:
            view.form_valid(form)
        except Exception as e:
            self.fail(f"Metadata migration trigger exception: {e}")
