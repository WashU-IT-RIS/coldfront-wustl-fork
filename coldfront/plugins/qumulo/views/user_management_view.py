from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from coldfront.plugins.qumulo.forms.UserManagementForm import UserManagementForm

import logging


class UserManagementView(LoginRequiredMixin, TemplateView):
    template_name = "user_management.html"
