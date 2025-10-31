from django.core.management.base import BaseCommand
from django.db.models import Q

from coldfront.core.allocation.models import AllocationStatusChoice, Allocation
from coldfront.core.resource.models import Resource


class Command(BaseCommand):
    help = "Run Check Billing Cycles to update billing cycles and prepaid expiration"

    def handle(self, *args, **options):
        print("Setting all Expired Storage allocations to Active")
        
        active_status = AllocationStatusChoice.objects.get(name="Active")
        expired_status = AllocationStatusChoice.objects.get(name="Expired")
        storage_resource = Resource.objects.filter(resource_type__name="Storage")
        
        Allocation.objects.filter(Q(status=expired_status) & Q(resources__in=storage_resource)).update(status=active_status, end_date=None)
       
        print("Done.")