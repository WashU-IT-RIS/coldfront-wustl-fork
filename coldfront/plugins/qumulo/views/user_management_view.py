from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import FormView

from coldfront.plugins.qumulo.forms import UserManagementForm


class UserManagementView(LoginRequiredMixin, FormView):
    form_class = UserManagementForm
    template_name = "user_management.html"
