from coldfront.core.allocation.models import Allocation
from coldfront.core.utils.common import import_from_settings
from coldfront.core.utils.mail import send_email_template
from coldfront.core.user.models import User
from coldfront.plugins.qumulo.utils.mail import (
    allocation_user_recipients_for_ris,
    email_template_context_for_service_desk,
)

def send_email_for_near_limit_allocation(allocation_data: dict):
    allocation = Allocation.objects.filter(pk=allocation_data['id'])[0]
    usage = allocation_data.get('usage', 0.0)
    limit = allocation_data.get('limit', 0.0)
    user_receiver_list = allocation_user_recipients_for_ris(allocation.project)

    subject = "Directory is close to its quota"
    template_path = "email/notify_users_with_allocations_near_limit.html"
    template_context = email_template_context_for_service_desk()
    template_context["addressee"] = allocation.project.pi.last_name
    template_context["usage"] = str(usage)
    template_context["limit"] = str(limit)
    with open('/tmp/near_limit.log', 'a') as nll:
        print(
            (
                f'Sending message with subject [subject] to users: '
                f'{user_receiver_list}.  Usage is {usage}, limit is {limit}.'
            ),
            file=nll
        )
    send_email_template(
        subject,
        template_path,
        template_context,
        get_email_sender(),
        user_receiver_list,
    )


def get_email_sender() -> str:
    return import_from_settings("DEFAULT_FROM_EMAIL")
