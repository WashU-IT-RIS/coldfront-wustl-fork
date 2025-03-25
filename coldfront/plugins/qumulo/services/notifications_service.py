from coldfront.core.allocation.models import Allocation
from coldfront.core.utils.common import import_from_settings
from coldfront.core.utils.mail import send_email_template
from coldfront.plugins.qumulo.utils.mail import (
    allocation_email_recipients_for_ris,
    ris_email_template_context,
)


def send_email_for_near_limit_allocation(allocation: Allocation):
    email_receiver_list = allocation_email_recipients_for_ris(allocation.project)
    subject = "Directory is close to its quota"
    template_path = "email/notify_users_with_allocations_near_limit.html"
    template_context = ris_email_template_context()
    # template_context["addressee"] = "Personne"
    # template_context["usage"] = "4.5"
    # template_context["usage_qualifier"] = "near"
    # template_context["limit"] = "5"
    send_email_template(
        subject,
        template_path,
        template_context,
        get_email_sender(),
        email_receiver_list,
    )


def get_email_sender() -> str:
    return import_from_settings("DEFAULT_FROM_EMAIL")
