from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import FormView
from coldfront.plugins.qumulo.forms.TriggerMigrationsForm import TriggerMigrationsForm
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.models import User

from django.urls import reverse

from coldfront.plugins.qumulo.services.itsm.migrate_to_coldfront import (
    MigrateToColdfront,
)
from coldfront.core.utils.mail import send_email_template, email_template_context
from coldfront.core.utils.common import import_from_settings


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

    def send_successful_metadata_migration_email(allocation) -> None:
        ctx = email_template_context()
        CENTER_BASE_URL = import_from_settings("CENTER_BASE_URL")
        ctx["allocation"] = allocation

        user_support_users = User.objects.filter(groups__name="RIS_UserSupport")
        user_support_emails = [user.email for user in user_support_users if user.email]

        send_email_template(
            subject="Metadata Migration Success",
            template_name="email/successful_metadata_migration.txt",
            template_context=ctx,
            sender=import_from_settings("DEFAULT_FROM_EMAIL"),
            receiver_list=user_support_emails,
        )

    def send_failed_metadata_migration_email(allocation, exception_output) -> None:
        ctx = email_template_context()

        CENTER_BASE_URL = import_from_settings("CENTER_BASE_URL")
        ctx["allocation"] = allocation
        ctx["exception_output"] = exception_output

        user_support_users = User.objects.filter(groups__name="RIS_UserSupport")
        user_support_emails = [user.email for user in user_support_users if user.email]

        send_email_template(
            subject="Metadata Migration Failed",
            template_name="email/failed_metadata_migration.txt",
            template_context=ctx,
            sender=import_from_settings("DEFAULT_FROM_EMAIL"),
            receiver_list=user_support_emails,
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
            TriggerMigrationsView.send_successful_metadata_migration_email(
                allocation_name
            )
        except Exception as e:
            display_message = str(e)
            messages.error(self.request, display_message)
            TriggerMigrationsView.send_failed_metadata_migration_email(
                allocation_name, display_message
            )

        return super().form_valid(form)

    def get_success_url(self):
        return reverse("qumulo:trigger-migrations")
