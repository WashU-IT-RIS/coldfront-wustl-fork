from typing import List, Optional


from coldfront.core.resource.models import Resource
from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttribute
)

from django.db.models import OuterRef, Subquery, Q


class ClientListItem:
    wustl_key: str
    email: str

class AllocationUserQueryService:
    @staticmethod
    def find_users_for_allocations(primary_allocation_ids: Optional[List[int]]) -> List[ClientListItem]:

        # NOTE: awkwardly, the connection between allocations and users
        # is *NOT* through the primary allocation, but through the associated RW/RO allocations
        resources = Resource.objects.filter(Q(name="rw") | Q(name="ro"))
        acl_allocations = Allocation.objects.filter(status__name="Active", resources__in=resources)

        primary_acl_alloc_sub_query = AllocationAttribute.objects.filter(
            allocation=OuterRef("pk"), allocation_attribute_type__name="storage_allocation_pk"
        ).values("value")[:1]

        acl_allocations = acl_allocations.annotate(
            primary_allocation_id=Subquery(primary_acl_alloc_sub_query),
        )

        if primary_allocation_ids:
            acl_allocations = acl_allocations.filter(primary_allocation_id__in=primary_allocation_ids)
        
        acl_allocations = acl_allocations.prefetch_related("allocationuser_set")

        for allocation in acl_allocations:
            for allocation_user in allocation.allocationuser_set.all():
                print(f"Username: {allocation_user.user.username}, Email: {allocation_user.user.email}")

        # Get all users associated with the allocations
        # users = User.objects.filter(resource__allocation__in=allocations).distinct()
        # writer = csv.writer(response)
        # writer.writerow(['WUSTL Key', "Allocation List"])

        # all_users = User.objects.exclude(is_staff=True)
        # for user in all_users:
        #     writer.writerow([user.username]) 
        # return response

