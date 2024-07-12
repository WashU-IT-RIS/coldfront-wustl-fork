from coldfront.core.allocation.models import AllocationStatusChoice
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("Adding Pending Allocation Status")
        AllocationStatusChoice.objects.get_or_create(name="Pending")
