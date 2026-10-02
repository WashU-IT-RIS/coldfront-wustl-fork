from coldfront.core.project.models import Project
from coldfront.core.user.models import User
from coldfront.core.utils.mail import email_template_context

import os


def email_template_context_for_service_desk() -> dict:
    template_context = email_template_context()
    template_context["service_desk_url"] = os.environ.get("SERVICE_DESK_URL")
    template_context["service_rate_categories_brouchure_url"] = os.environ.get(
        "SERVICE_RATE_CATEGORIES_BROUCHURE_URL"
    )
    template_context["ris_home_url"] = os.environ.get("RIS_HOME_URL")
    return template_context


def allocation_user_recipients_for_ris(project: Project) -> list[User]:
    receiver_list = []

    for allocation in project.allocation_set.all():
        receiver_list.extend(
            allocation.allocationuser_set.exclude(
                status__name__in=["Removed", "Error"]
            ).values_list("user__email", flat=True)
        )

    return receiver_list
