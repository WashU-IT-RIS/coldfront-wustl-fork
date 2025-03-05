from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView
from coldfront.plugins.qumulo.forms import TriggerMigrationsForm


class TriggerMigrationsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "trigger_migrations.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["trigger_migrations_form"] = TriggerMigrationsForm()
        return context

    def test_func(self):
        return self.request.user.is_staff
