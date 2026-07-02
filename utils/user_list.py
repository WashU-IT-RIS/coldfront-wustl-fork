import os
import sys

from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttribute,
    AllocationAttributeType,
    AllocationUser,
)
from coldfront.core.project.models import Project
from coldfront.core.resource.models import Resource
from coldfront.core.user.models import User

def get_request_type():
    rtype = os.environ.get("USER_LIST_PI_ONLY", False)
    if rtype is False or rtype.lower() == 'false':
        return False
    return True

request_pi_only = get_request_type()
requested_storage_resource = os.environ.get("USER_LIST_RESOURCE", None)
storage_resources_qs = Resource.objects.filter(resource_type__name="Storage")
if (
    not requested_storage_resource
    or not storage_resources_qs.filter(name=requested_storage_resource).exists()
):
    storage_resource_names = storage_resources_qs.values_list("name", flat=True)
    print(
        "Invalid USER_LIST_RESOURCE configuration: "
        f"got USER_LIST_RESOURCE={requested_storage_resource!r}; "
        f"expected one of: {', '.join(storage_resource_names)}. "
        "Please set the USER_LIST_RESOURCE environment variable to a valid storage resource name."
    )
    sys.exit(1)

emails = []
no_emails = []
allocation_pis = {}
storage_allocation_pk_type = AllocationAttributeType \
                                .objects \
                                .filter(name='storage_allocation_pk')[0].id
for allocation in Allocation.objects.filter(
    resources__name=requested_storage_resource
):
    if request_pi_only:
        project = Project.objects.filter(pk=allocation.project_id)[0]
        pi = User.objects.filter(pk=project.pi_id)[0]
        allocation_pis[str(allocation).split(' ')[-1].strip('()')] = pi

    for attribute in AllocationAttribute.objects.filter(
        allocation_attribute_type_id=storage_allocation_pk_type,
        value=allocation.pk
    ):
        acl_allocation_id = attribute.allocation_id

        for allocation_user in AllocationUser.objects.filter(
            allocation_id=acl_allocation_id
        ):
            user = User.objects.get(pk=allocation_user.user_id)
            if "@" in user.email:
                emails.append(user.email)
                continue
            no_emails.append(user.username)


if request_pi_only:
    with open(
        f'/tmp/{requested_storage_resource}-AllocationPIs.csv',
        'w'
    ) as apis_txt:
        for alloc, pi in allocation_pis.items():
            apis_txt.write(f'{alloc},{pi}\n')
else:
    print("######################################")
    print("# User e-mail addresses:             #")
    print("######################################")
    email_set = set(emails)
    for email in email_set:
        print(email)

    if len(no_emails) > 0:
        print("######################################")
        print("# User IDs without e-mail addresses: #")
        print("######################################")
        for user_id in set(no_emails):
            print(user_id)
sys.exit(0)
