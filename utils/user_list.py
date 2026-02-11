import os
import sys

from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttribute,
    AllocationUser,
)
from coldfront.core.resource.models import Resource
from coldfront.core.user.models import User

requested_storage_resource = os.environ.get("USER_LIST_RESOURCE", None)
storage_resource_names = Resource.objects.filter(
    resource_type__name="Storage"
).values_list("name", flat=True)
if requested_storage_resource not in storage_resource_names:
    print(
        f"USER_LIST_RESOURCE value should be one of: {', '.join(storage_resource_names)}"
    )
    sys.exit(1)

emails = []
no_emails = []
for allocation in Allocation.objects.filter(resources__name=requested_storage_resource):
    # TODO: optimize this query to avoid N+1 queries, maybe by using select_related or prefetch_related
    #
    # allocation_ids = Allocation.objects.filter(
    #                       resources__name=requested_storage_resource, 
    #                       status__name="Active")
    #                       .values_list("id", flat=True)
    # user_group_allocations = Allocation.objects.filter(
    #    allocationattribute__allocation_attribute_type__name="storage_allocation_pk",
    #    allocationattribute__value__in=allocation_ids,
    # ).prefetch_related("allocationattribute_set__allocationuser_set__user")
    # for user_group_allocation in user_group_allocations:
    #     for attribute in user_group_allocation.allocationattribute_set.all():
    #         if attribute.allocation_attribute_type.name == "storage_allocation_pk":
    #             for allocation_user in attribute.allocationuser_set.all():
    #                 user = allocation_user.user
    #                 if "@" in user.email:
    #                     emails.append(user.email)
    #                 else:
    #                     no_emails.append(user.username)
    # I don't have time now to test the above code.
    #
    # The query AllocationAttribute.objects.filter(value=allocation.pk) relies on a value that is
    # the primary key of the allocation, which is an integer. This is a bit brittle and relies on
    # the assumption that there are no other allocation attributes with integer values that could match this.

    for attribute in AllocationAttribute.objects.filter(value=allocation.pk):
        acl_allocation_id = attribute.allocation_id
        for allocation_user in AllocationUser.objects.filter(
            allocation_id=acl_allocation_id
        ):
            user = User.objects.get(pk=allocation_user.user_id)
            if "@" in user.email:
                emails.append(user.email)
            else:
                no_emails.append(user.username)

for email in set(emails):
    print(email)

if len(no_emails) > 0:
    print("######################################")
    print("# User IDs without e-mail addresses: #")
    print("######################################")
    for user_id in set(no_emails):
        print(user_id)

sys.exit(0)
