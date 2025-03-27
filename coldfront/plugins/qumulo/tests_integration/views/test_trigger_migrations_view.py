from coldfront.plugins.qumulo.forms import TriggerMigrationsForm
from unittest.mock import patch, MagicMock
from django.contrib import messages

from coldfront.plugins.qumulo.views.trigger_migrations_view import TriggerMigrationsView

from django.test import TestCase, tag, RequestFactory
from coldfront.core.test_helpers.factories import UserFactory
from coldfront.plugins.qumulo.tests.fixtures import create_allocation_assets


class TriggerMigrationsViewTests(TestCase):
    def setUp(self) -> None:
        create_allocation_assets()

    @tag("integration")
    def testMigrationSuccessfulWithValidAllocation(
        self,
    ):
        success = True

        valid_data = {"allocation_name_search": "/vol/rdcw-fs1/kchoi"}
        messages.add_message = MagicMock()
        request = RequestFactory().get(
            "src/coldfront.plugins.qumulo/views/trigger_migrations_view.py"
        )
        user = UserFactory(is_staff=True)
        form = TriggerMigrationsForm(data=valid_data)
        form.is_valid()
        view = TriggerMigrationsView()
        request.user = user
        view.request = request
        try:
            view.form_valid(form)
        except:
            success = False
        self.assertEqual(success, True)

    @tag("integration")
    def testMigrationFailWithInvalidAllocation(self):
        success = True
        invalid_data = {"allocation_name_search": "allocation"}
        form = TriggerMigrationsForm(data=invalid_data)
        form.is_valid()
        view = TriggerMigrationsView()
        try:
            view.form_valid(form)
        except:
            success = False
        self.assertEqual(success, False)
