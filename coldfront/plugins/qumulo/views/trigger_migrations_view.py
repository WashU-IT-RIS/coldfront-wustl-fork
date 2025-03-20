from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import FormView
from coldfront.plugins.qumulo.forms import TriggerMigrationsForm
from django.http import HttpResponse

from django.urls import reverse

from coldfront.plugins.qumulo.services.itsm.migrate_to_coldfront import (
    MigrateToColdfront,
)


class TriggerMigrationsView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = "trigger_migrations.html"
    form_class = TriggerMigrationsForm

    def test_func(self):
        # TODO: chnage superuser to reflect user support role when present in prod
        return (
            self.request.user.is_staff
            or self.request.user.is_superuser
            or self.request.user.has_perm("allocation.can_add_allocation")
        )

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["trigger_migrations_form"] = TriggerMigrationsForm()
        return context

    def form_valid(self, form: TriggerMigrationsForm):
        allocation_name = form.cleaned_data["allocation_name_search"]
        migrate_from_itsm_to_coldfront = MigrateToColdfront()

        migrate_from_itsm_to_coldfront.by_storage_provision_name(allocation_name)

        return super().form_valid(form)

    def get_success_url(self):
        return reverse("qumulo:trigger-migrations")
