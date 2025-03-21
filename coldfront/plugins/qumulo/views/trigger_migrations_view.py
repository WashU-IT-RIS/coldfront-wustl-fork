from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import FormView
from coldfront.plugins.qumulo.forms import TriggerMigrationsForm
from django.http import HttpResponse
from django.contrib import messages

from django.urls import reverse

from coldfront.plugins.qumulo.services.itsm.migrate_to_coldfront import (
    MigrateToColdfront,
)
from coldfront.plugins.qumulo.tasks import (
    __send_successful_metadata_migration_email,
    __send_failed_metadata_migration_email,
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
        display_message = "Allocation metadata migrated"
        try:
            migrate_from_itsm_to_coldfront.by_storage_provision_name(allocation_name)
            messages.success(self.request, display_message)
            __send_successful_metadata_migration_email(allocation_name)
        except Exception as e:
            display_message = str(e)
            messages.error(self.request, display_message)
            __send_failed_metadata_migration_email(allocation_name, display_message)

        return super().form_valid(form)

    def get_success_url(self):
        return reverse("qumulo:trigger-migrations")
