from django.core.management.base import BaseCommand
from coldfront.core.allocation.models import AllocationAttribute, Allocation


class Command(BaseCommand):

    def change_subscription_to_consumption(self):
        subscription_allocations = Allocation.objects.filter(status__name__in=['Active', 'New', 'Pending'],allocationattribute__allocation_attribute_type__name="service_rate_category", allocationattribute__value="subscription").values("pk")
        subscription_service_rate_attributes = AllocationAttribute.objects.filter(allocation_attribute_type__name="service_rate_category", value="subscription").filter(allocation__in=subscription_allocations)
        
        subscription_service_rate_attributes.update(value="consumption")

    def handle(self, *args, **options):
        print("Changing all Subscription Service Rate Categories to Consumption")
        self.change_subscription_to_consumption()