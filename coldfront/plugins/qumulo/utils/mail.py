import logging
import os

from coldfront.core.project.models import Project
from coldfront.core.user.models import User
from coldfront.core.utils.common import import_from_settings
from coldfront.core.utils.mail import email_template_context

from django.conf import settings
from django.core.mail import EmailMessage, send_mail
from django.template.loader import render_to_string

from smtplib import SMTPException

logger = logging.getLogger(__name__)
EMAIL_DEVELOPMENT_EMAIL_LIST = import_from_settings(
        "EMAIL_DEVELOPMENT_EMAIL_LIST"
)
EMAIL_ENABLED = import_from_settings("EMAIL_ENABLED", False)

def email_template_context_for_service_desk() -> dict:
    template_context = email_template_context()
    template_context["service_desk_url"] = os.environ.get("SERVICE_DESK_URL")
    template_context["service_rate_categories_brouchure_url"] = os.environ.get(
        "SERVICE_RATE_CATEGORIES_BROUCHURE_URL"
    )
    return template_context


def allocation_user_recipients_for_ris(project: Project) -> list[User]:
    receiver_list = []

    for allocation in project.allocation_set.all():
        receiver_list.extend(
            allocation.allocationuser_set.exclude(
                status__name__in=["Removed", "Error"]
            ).values_list("user__email", flat=True)
        )

    # bmulligan 20261009: this was "necessary" because QA testing was
    # returning duplicate and bogus recipients in "receiver_list."  the
    # bogus recipient address was a literal "[]".
    return list(
        sorted(
            set(
                list(
                    filter(
                        lambda x: '@' in x,
                        receiver_list
                    )
                )
            )
        )
    )

def send_email(subject, body, sender, receiver_list, cc=[]):
    """Helper function for sending emails"""

    if not EMAIL_ENABLED:
        return

    if len(receiver_list) == 0:
        logger.error("Failed to send email missing receiver_list")
        return

    if len(sender) == 0:
        logger.error("Failed to send email missing sender address")
        return

    if settings.DEBUG:
        receiver_list = EMAIL_DEVELOPMENT_EMAIL_LIST

    if cc and settings.DEBUG:
        cc = EMAIL_DEVELOPMENT_EMAIL_LIST

    try:
        if cc:
            email = EmailMessage(subject, body, sender, receiver_list, cc=cc)
            email.send(fail_silently=False)
        else:
            send_mail(subject, body, sender, receiver_list, fail_silently=False)
    except SMTPException as e:
        logger.error(
            "Failed to send email to %s from %s with subject %s",
            sender,
            ",".join(receiver_list),
            subject,
        )

def send_email_template(
    subject, template_name, template_context, sender, receiver_list
):
    """Helper function for sending emails from a template"""
    if not EMAIL_ENABLED:
        return

    body = render_to_string(template_name, template_context)

    return send_email(subject, body, sender, receiver_list)

