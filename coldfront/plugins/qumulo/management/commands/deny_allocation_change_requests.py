from django.core.management.base import BaseCommand
from coldfront.core.allocation.models import AllocationChangeRequest, AllocationAttributeChangeRequest, AllocationChangeStatusChoice

class Command(BaseCommand):
    help = 'Delete all pending allocation change requests from the database.'

    def handle(self, *args, **options):
        pending_status = AllocationChangeStatusChoice.objects.get(name="Pending")
        denied_status = AllocationChangeStatusChoice.objects.get(name="Denied")
        pending_requests = AllocationChangeRequest.objects.filter(status=pending_status)
        count = pending_requests.count()
        pending_requests.update(status=denied_status)
        print(f"Denied {count} pending allocation change request(s).")