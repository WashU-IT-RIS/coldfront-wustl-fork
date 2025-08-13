from django.core.management.base import BaseCommand
from coldfront.core.allocation.models import AllocationChangeRequest

class Command(BaseCommand):
    help = 'Delete all pending allocation change requests from the database.'

    def handle(self, *args, **options):
        pending_requests = AllocationChangeRequest.objects.filter(status='pending')
        count = pending_requests.count()
        pending_requests.delete()
        print(f"Deleted {count} pending allocation change request(s).")