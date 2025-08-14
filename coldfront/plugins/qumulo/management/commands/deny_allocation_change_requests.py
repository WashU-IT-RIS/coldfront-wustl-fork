from django.core.management.base import BaseCommand
from coldfront.core.allocation.models import AllocationChangeRequest, AllocationAttributeChangeRequest

class Command(BaseCommand):
    help = 'Delete all pending allocation change requests from the database.'

    def handle(self, *args, **options):
        pending_requests = AllocationChangeRequest.objects.filter(status__name='Pending')
        count = pending_requests.count()
        pending_requests.update(status__name='Denied')
        print(f"Denied {count} pending allocation change request(s).")