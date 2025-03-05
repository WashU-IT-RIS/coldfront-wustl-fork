from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.http import (
    HttpResponse,
)
from django.urls import reverse


class TriggerMigrationsView(LoginRequiredMixin, View):

    def get_success_url(self):
        return reverse("trigger-migrations")
