from django.core.management.base import BaseCommand

from django_q.tasks import async_chain

from coldfront.plugins.qumulo.tasks import (
    poll_ad_groups,
    conditionally_update_storage_allocation_statuses,
)
from typing import List
import csv

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import EmptyPage, Paginator
from django.views.generic import View
from django.http import HttpResponse


from coldfront.core.user.models import (
    User
)
from coldfront.core.resource.models import Resource
from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttribute
)

from django.db.models import OuterRef, Subquery


class Command(BaseCommand):
    help = (
        "HIJACKED"
    )

    def handle(self, *args, **options):
        print("Running allocation check")
        import pdb
        pdb.set_trace()
        

        primary_allocation_id = "100000"
        # NOTE: awkwardly, the connection between allocations and users
        # is *NOT* through the primary allocation, but through the associated RW/RO allocations
        resources = Resource.objects.filter(Q(name="rw") | Q(name="ro"))
        acl_allocations = Allocations.objects.filter(status__name="Active")

        primary_acl_alloc_sub_query = AllocationAttribute.objects.filter(
            allocation=OuterRef("pk"), allocation_attribute_type__name="storage_allocation_pk"
        ).values("value")[:1]

        acl_allocations = acl_allocations.annotate(
            primary_allocation_id=Subquery(prepaid_exp_sub_query),
        )

        if primary_allocation_id:
            acl_allocations = acl_allocations.filter(primary_allocation_id=primary_allocation_id)
        

        # Get all users associated with the allocations
        # users = User.objects.filter(resource__allocation__in=allocations).distinct()
        # writer = csv.writer(response)
        # writer.writerow(['WUSTL Key', "Allocation List"])

        # all_users = User.objects.exclude(is_staff=True)
        # for user in all_users:
        #     writer.writerow([user.username]) 
        # return response

