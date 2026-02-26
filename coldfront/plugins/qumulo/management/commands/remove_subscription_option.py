from coldfront.core.allocation.models import AllocationAttribute

def change_subscription_to_consumption():
    
    subscription_service_rate_attributes = AllocationAttribute.objects.filter(allocation_attribute_type__name="service_rate_category", value="subscription")

    for attribute in subscription_service_rate_attributes:
        attribute.value = "consumption"
        attribute.save()