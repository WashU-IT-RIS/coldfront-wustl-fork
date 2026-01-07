import os
import sys

from coldfront.core.allocation.models import Allocation, AllocationAttribute, AllocationUser
from coldfront.core.resource.models import Resource
from coldfront.core.user.models import User

rpt_resource = os.environ.get('USER_LIST_RESOURCE', None)
if rpt_resource not in ['Storage2', 'Storage3']:
    print("USER_LIST_RESOURCE value should be one of: Storage2, Storage3")
    sys.exit(1)
r = Resource.objects.filter(name=rpt_resource)[0]
no_emails = []
for allocation in Allocation.objects.all():
    if allocation.get_parent_resource != r:
        continue
    for attribute in AllocationAttribute.objects.filter(value=allocation.pk):
        acl_allocation_id = attribute.allocation_id
        for allocation_user in \
            AllocationUser.objects.filter(allocation_id=acl_allocation_id):
                user = User.objects.get(pk=allocation_user.user_id)
                if '@' in user.email:
                    print(user.email)
                else:
                    no_emails.append(user.username)
if len(no_emails) > 0:
    print('######################################')
    print('# User IDs without e-mail addresses: #')
    print('######################################')
    for user_id in no_emails:
        print(user_id)
sys.exit(0)
