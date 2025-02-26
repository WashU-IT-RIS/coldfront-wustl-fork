from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import FormView

from coldfront.plugins.qumulo.forms.UserManagementForm import UserManagementForm

import logging


class UserManagementView(LoginRequiredMixin, FormView):
    form_class = UserManagementForm
    template_name = "user_management.html"

    def form_valid(self, form):
        logging.warning(f"UserManagementView form_valid: {form.cleaned_data}")
        return super().form_valid(form)
