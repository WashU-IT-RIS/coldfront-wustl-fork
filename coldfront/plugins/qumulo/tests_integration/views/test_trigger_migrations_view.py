from django.contrib import messages
from django.test import TestCase, tag, RequestFactory

from coldfront.plugins.qumulo.forms.TriggerMigrationsForm import TriggerMigrationsForm
from coldfront.plugins.qumulo.views.trigger_migrations_view import TriggerMigrationsView
from coldfront.plugins.qumulo.tests.fixtures import create_allocation_assets

from unittest.mock import MagicMock


class TriggerMigrationsViewTests(TestCase):
    def set_up(self) -> None:
        create_allocation_assets()

    @tag("integration")
    def test_migration_successful_with_valid_allocation(
        self,
    ):
        success = None
        messages.success = MagicMock()
        request = RequestFactory().get(
            "src/coldfront.plugins.qumulo/views/trigger_migrations_view.py"
        )
        valid_data = {"allocation_name_search": "/vol/rdcw-fs1/kchoi"}
        form = TriggerMigrationsForm(data=valid_data)
        view = TriggerMigrationsView()
        view.request = request
        try:
            view.form_valid(form)
            success = True
        except:
            success = False
        self.assertEqual(success, True)

    @tag("integration")
    def test_migration_fail_with_invalid_allocation(self):
        success = None
        messages.error = MagicMock()
        request = RequestFactory().get(
            "src/coldfront.plugins.qumulo/views/trigger_migrations_view.py"
        )
        invalid_data = {"allocation_name_search": "allocation"}
        form = TriggerMigrationsForm(data=invalid_data)
        view = TriggerMigrationsView()
        view.request = request
        try:
            view.form_valid(form)
            success = True
        except:
            success = False
        self.assertEqual(success, True)
