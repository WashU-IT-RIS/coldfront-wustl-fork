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
from utils.coldfront_ad_utils import ColdfrontAdUtils

def get_request_type():
    rtype = os.environ.get("USER_LIST_ID_ONLY", False)
    if rtype is False or rtype.lower() == 'false':
        return False
    return True

ad_utils = None
request_id_only = get_request_type()
if request_id_only:
    ad_utils = ColdfrontAdUtils()
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
    if request_id_only:
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
            if "@" in user.email and not request_id_only:
                emails.append(user.email)
                continue

            if request_id_only:
                resolved_id = ad_utils.resolve_id(user.username)
                if resolved_id['id_is_user']:
                    no_emails.append(user.username)
                elif resolved_id['id_is_group']:
                    no_emails.extend(
                        list(
                            ad_utils._process_group_members(
                                list(resolved_id['data'])
                            )
                        )
                    )
            else:
                no_emails.append(user.username)


if request_id_only:
    with open(
            f'/tmp/{requested_storage_resource}-UserList.csv',
            'w'
    ) as ul_txt:
        for user_id in set(no_emails):
            ul_txt.write(f'{user_id}\n')
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
