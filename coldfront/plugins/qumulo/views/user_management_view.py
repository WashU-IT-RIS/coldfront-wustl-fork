from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import HttpResponse, HttpRequest

from coldfront.plugins.qumulo.forms.UserManagementForm import UserManagementForm

import logging


class UserManagementView(LoginRequiredMixin, TemplateView):
    template_name = "user_management.html"

    def post(self, request: HttpRequest, *args, **kwargs):
        logging.warning("posted")

        return HttpResponse("posted")
