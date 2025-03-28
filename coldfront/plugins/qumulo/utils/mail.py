from coldfront.core.project.models import Project
from coldfront.core.utils.common import import_from_settings
from coldfront.core.utils.mail import email_template_context

import os


def ris_email_template_context() -> dict:
    template_context = email_template_context()
    template_context["service_desk_url"] = os.environ.get("SERVICE_DESK_URL")
    template_context["service_rate_categories_brouchure_url"] = os.environ.get(
        "SERVICE_RATE_CATEGORIES_BROUCHURE_URL"
    )
    template_context["ris_home_url"] = os.environ.get("RIS_HOME_URL")
    return template_context


def allocation_email_recipients_for_ris(project: Project) -> list[str]:
    receiver_list = []

    for allocation in project.allocation_set.all():
        receiver_list.extend(
            allocation.allocationuser_set.exclude(
                status__name__in=["Removed", "Error"]
            ).values_list("user__email", flat=True)
        )

    return receiver_list
