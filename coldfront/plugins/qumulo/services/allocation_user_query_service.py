from typing import List, Optional


from coldfront.core.resource.models import Resource
from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttribute,
    AllocationUser
)
from coldfront.core.user.models import User

from django.db.models import OuterRef, Subquery, Q, Prefetch, F, Value
from django.db.models.functions import Concat


class ClientListItem:
    wustl_key: str
    email: str

class AllocationUserQueryService:

    @staticmethod
    def get_all_users_with_allocation_info() -> List[ClientListItem]:
        import pdb
        pdb.set_trace()
        storage_name_subquery = AllocationAttribute.objects.filter(
            allocation=OuterRef('allocation'),
            allocation_attribute_type__name='storage_name'
        ).values('value')[:1]

        all_users = AllocationUser.objects.filter(user__is_staff=False).prefetch_related(
            Prefetch(
                'allocation',
                queryset=Allocation.objects.annotate(
                    allocation_id=F('id')
            ).only('id'),
            to_attr='allocations'
            )
        ).annotate(
            wustl_key=F('user__username'),
            email=F('user__email'),
            storage_name=Subquery(storage_name_subquery)
        )

        pdb.set_trace()

        result = [
            ClientListItem(
            wustl_key=user.wustl_key,
            email=user.email
            )
            for user in all_users
        ]
        return result

        pdb.set_trace()

        

        
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

