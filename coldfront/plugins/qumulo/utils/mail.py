from coldfront.core.project.models import Project


def allocation_email_recipients_for_ris(project: Project) -> list[str]:
    receiver_list = []

    for allocation in project.allocation_set.all():
        receiver_list.extend(
            allocation.allocationuser_set.exclude(
                status__name__in=["Removed", "Error"]
            ).values_list("user__email", flat=True)
        )

    return receiver_list
