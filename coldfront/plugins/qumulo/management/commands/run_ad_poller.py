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

from django.db.models import OuterRef, Subquery, Q


class Command(BaseCommand):
    help = (
        "HIJACKED"
    )

    def handle(self, *args, **options):
        print("Running allocation check")
        from coldfront.plugins.qumulo.services.allocation_user_query_service import AllocationUserQueryService

        service = AllocationUserQueryService()

        import pdb
        pdb.set_trace()

