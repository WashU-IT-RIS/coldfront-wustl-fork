import logging

from django.template.loader import render_to_string

from coldfront.config.env import ENV
from coldfront.core.utils.common import import_from_settings
from coldfront.core.utils.mail import (
    EMAIL_ENABLED,
    EMAIL_SENDER,
    email_template_context,
    send_acl_reset_email,
    send_email,
)

logger = logging.getLogger(__name__)

EMAIL_ON_CALL = import_from_settings("EMAIL_ON_CALL", "")


def acl_reset_complete_hook(task_object):
    if EMAIL_ENABLED:
        send_acl_reset_email(task_object)


def notify_on_call_on_failure_hook(task_object):
    """
    django-q hook: email the on-call address when a task fails.
    On failure django-q stores "<error> : <traceback>" in task_object.result.
    """
    if task_object.success:
        return
    if not EMAIL_ON_CALL:
        logger.error(
            f"Task {task_object.name} failed but EMAIL_ON_CALL is not set; "
            f"no failure email sent. Result: {task_object.result}"
        )
        return

    subject = f"Scheduled task failed: {task_object.name}"
    body = "\n".join(
        [
            f"Task: {task_object.name}",
            f"Function: {task_object.func}",
            f"Task ID: {task_object.id}",
            f"Arguments: {task_object.args}",
            f"Keyword arguments: {task_object.kwargs}",
            f"Started: {task_object.started}",
            f"Stopped: {task_object.stopped}",
            "",
            "Error and stack trace:",
            "",
            str(task_object.result),
        ]
    )
    send_email(subject, body, EMAIL_SENDER, [EMAIL_ON_CALL])
