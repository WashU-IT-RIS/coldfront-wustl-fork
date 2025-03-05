from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView


class TriggerMigrationsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "trigger_migrations.html"

    def test_func(self):
        return self.request.user.is_staff
