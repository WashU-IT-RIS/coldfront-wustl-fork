import coldfront.plugins.qumulo.settings as qumulo_settings

from coldfront.core.allocation.models import Allocation
from coldfront.core.utils.common import import_from_settings
from coldfront.core.utils.mail import send_email_template
from coldfront.core.user.models import User
from coldfront.plugins.qumulo.utils.mail import (
    allocation_user_recipients_for_ris,
    email_template_context_for_service_desk,
)
from pint import UnitRegistry

def compact_bytes(bytes_value, override_plurals=False):
    def override(q):
        return (q._magnitude == 1.0) or override_plurals
    quantity = (float(bytes_value) * UnitRegistry().byte).to_compact()
    return_string = f'{quantity._magnitude:0.02f} {str(quantity._units)}'
    if not override(quantity):
        return_string += 's'
    return return_string

def send_email_for_near_limit_allocation(allocation_data: dict):
    allocation = Allocation.objects.filter(pk=allocation_data['id'])[0]
    user_receiver_list = allocation_user_recipients_for_ris(allocation.project)

    subject = "Directory is close to its quota"
    template_path = "email/notify_users_with_allocations_near_limit.txt"

    template_context = email_template_context_for_service_desk()
    template_context["storage_name"] = allocation_data.get('storage_name')
    template_context["storage_path"] = allocation_data.get(
        'allocationattribute__value'
    )

    template_context["addressee"] = '{} {}'.format(
        allocation.project.pi.first_name,
        allocation.project.pi.last_name
    )
    template_context["usage"] = compact_bytes(
        allocation_data.get('usage', '0.0')
    )
    template_context["limit"] = compact_bytes(
        allocation_data.get('quota', '0.0'),
        True
    )

    send_email_template(
        subject,
        template_path,
        template_context,
        get_email_sender(),
        user_receiver_list,
    )


def get_email_sender() -> str:
    # bmulligan 20261009: this needs to get reverted before production
    # deployment
    # return import_from_settings("DEFAULT_FROM_EMAIL")
    return 'No Reply <noreply@gowustl.onmicrosoft.com>'
