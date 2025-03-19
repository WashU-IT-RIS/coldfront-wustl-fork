from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView
from coldfront.plugins.qumulo.forms import TriggerMigrationsForm

from django.urls import reverse

from coldfront.plugins.qumulo.services.itsm.migrate_to_coldfront import (
    MigrateToColdfront,
)

from django.test import TestCase
from django.urls.exceptions import NoReverseMatch
from unittest.mock import patch, MagicMock


class TriggerMigrationsViewTests(TestCase):
    def testOne():
        return True
