import textwrap

from django.template.loader import render_to_string

from coldfront.config.env import ENV
from coldfront.core.utils.mail import (
    EMAIL_ENABLED,
    EMAIL_SENDER,
    email_template_context,
    send_acl_reset_email,
)


def acl_reset_complete_hook(task_object):
    if EMAIL_ENABLED:
        send_acl_reset_email(task_object)
    else:
        ctx = email_template_context()
        ctx["task_duration"] = "{:.2f}".format(task_object.time_taken())
        ctx["task_name"] = task_object.name
        ctx["allocation_name"] = allocation_name = task_object.args[1].get_attribute(
            "storage_name"
        )
        if task_object.success:
            ctx["task_error_message"] = task_object.result
            subject = f"Sucessful ACL Reset for Allocation {allocation_name}"
            template = "email/allocation_acl_reset_success.txt"
        else:
            subject = f"ACL Reset Failure for Allocation {allocation_name}"
            template = "email/allocation_acl_reset_failure.txt"
        log_file = ENV.str("ACL_RESET_MSG_LOG", default="/tmp/e-mail_notifications.log")
        with open(log_file, "a") as emnl:
            emnl.write(
                (
                    f"To: {task_object.args[0]}\n"
                    f"From: {EMAIL_SENDER}\n"
                    f"Subject: {subject}\n\n"
                    f"{render_to_string(template, ctx)}"
                    "######################################################\n"
                )
            )
