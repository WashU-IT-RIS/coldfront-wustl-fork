from django.test import TestCase, Client
from django.db.models import OuterRef, Subquery

from coldfront.plugins.qumulo.tests.utils.mock_data import (
    build_models,
    default_form_data,
    create_allocation
)
from coldfront.core.resource.models import Resource
from coldfront.core.allocation.models import (
    Allocation,
    AllocationStatusChoice,
    AllocationAttribute,
)

from coldfront.plugins.qumulo.management.commands.remove_subscription_option import change_subscription_to_consumption

class TestRemoveSubscriptionOption(TestCase):
    def setUp(self):
        self.client = Client()

        build_data = build_models()

        self.project = build_data["project"]
        self.user = build_data["user"]

        self.no_subscription_form_data = default_form_data
        default_form_data["service_rate_category"] = "subscription"
        self.subscription_form_data = default_form_data

        self.client.force_login(self.user)

    def filter_allocations_by_service_rate_category(self):
        storage_resources = Resource.objects.filter(resource_type__name="Storage")
        allocations = Allocation.objects.filter(status__name="Active", resources__in=storage_resources)

        service_rate_category_sub_query = AllocationAttribute.objects.filter(
            allocation=OuterRef("pk"),
            allocation_attribute_type__name="service_rate_category",
        ).values("value")[:1]

        allocations = allocations.annotate(
            service_rate_category=Subquery(service_rate_category_sub_query)
        )

        subscription_allocations = allocations.filter(service_rate_category="subscription")
        consumption_allocations = allocations.filter(service_rate_category="consumption")
        return subscription_allocations, consumption_allocations

    def test_one_subscription_allocation(self):
        non_subscription_allocation = create_allocation(self.project, self.user, self.no_subscription_form_data)
        subscription_allocation = create_allocation(self.project, self.user, self.subscription_form_data)
        subscription_allocation.status = AllocationStatusChoice.objects.get(name="Active")
        subscription_allocation.save()
        non_subscription_allocation.status = AllocationStatusChoice.objects.get(name="Active")
        non_subscription_allocation.save()
        
        
        change_subscription_to_consumption()

        subscription_allocations, consumption_allocations = self.filter_allocations_by_service_rate_category()
        
        self.assertEqual(subscription_allocations.count(), 0)
        self.assertEqual(consumption_allocations.count(), 2)
    

    def test_no_subscription_allocations(self):
        allocation_one = create_allocation(self.project, self.user, self.no_subscription_form_data)
        allocation_two = create_allocation(self.project, self.user, self.no_subscription_form_data)
        allocation_one.status = AllocationStatusChoice.objects.get(name="Active")
        allocation_one.save()
        allocation_two.status = AllocationStatusChoice.objects.get(name="Active")
        allocation_two.save()

        change_subscription_to_consumption()

        subscription_allocations, consumption_allocations = self.filter_allocations_by_service_rate_category()
        
        self.assertEqual(subscription_allocations.count(), 0)
        self.assertEqual(consumption_allocations.count(), 2)