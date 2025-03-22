from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView
from coldfront.plugins.qumulo.forms import TriggerMigrationsForm

from django.urls import reverse

from coldfront.plugins.qumulo.views.trigger_migrations_view import TriggerMigrationsView

from django.test import TestCase
from django.urls.exceptions import NoReverseMatch
from unittest.mock import patch, MagicMock


class TriggerMigrationsViewTests(TestCase):
    def testMigrationSuccessfulWithValidAllocation(self):
        success = True
        valid_data = {"allocation_name_search": "/vol/rdcw-fs1/tychsen"}
        form = TriggerMigrationsForm(data=valid_data)
        form.is_valid()
        view = TriggerMigrationsView()
        try:
            breakpoint()
            view.form_valid(form)
        except:
            success = False
        self.assertEqual(success, True)

    def testMigrationFailWithInvalidAllocation(self):
        invalid_data = {"allocation_name_search": "allocation"}
        form = TriggerMigrationsForm(data=invalid_data)
        form.is_valid()
        view = TriggerMigrationsView()
        try:
            view.form_valid(form)
        except:
            pass
        self.assertNotEqual(view.display_message, "Allocation metadata migrated")
