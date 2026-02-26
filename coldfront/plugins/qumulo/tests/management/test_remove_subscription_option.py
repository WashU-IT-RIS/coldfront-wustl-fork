from django.test import TestCase, Client

from coldfront.plugins.qumulo.tests.utils.mock_data import (
    build_models,
    default_form_data,
    create_allocation
)
from coldfront.core.allocation.models import (
    Allocation,
)

from coldfront.plugins.qumulo.management.commands.remove_subscription_option import change_subscription_to_consumption

class TestRemoveSubscriptionOption(TestCase):
    def setUp(self):
        self.client = Client()

        build_data = build_models()

        self.project = build_data["project"]
        self.user = build_data["user"]

        self.no_subscription_form_data = default_form_data.copy()
        self.subscription_form_data = default_form_data.copy()
        self.no_subscription_form_data["service_rate_category"] = "consumption"
        self.subscription_form_data["service_rate_category"] = "subscription"

        self.client.force_login(self.user)

    def test_one_subscription_allocation(self):
        non_subscription_allocation = create_allocation(self.project, self.user, self.no_subscription_form_data)
        subscription_allocation = create_allocation(self.project, self.user, self.subscription_form_data)

        change_subscription_to_consumption()

        subscription_allocations = Allocation.objects.filter(allocationattribute__allocation_attribute_type__name="service_rate_category", allocationattribute__value="subscription").values("pk")
        consumption_allocations = Allocation.objects.filter(allocationattribute__allocation_attribute_type__name="service_rate_category", allocationattribute__value="consumption").values("pk")

        self.assertEqual(subscription_allocations.count(), 0)
        self.assertEqual(consumption_allocations.count(), 2)
    

    def test_no_subscription_allocations(self):
        allocation_one = create_allocation(self.project, self.user, self.no_subscription_form_data)
        allocation_two = create_allocation(self.project, self.user, self.no_subscription_form_data)

        change_subscription_to_consumption()

        subscription_allocations = Allocation.objects.filter(allocationattribute__allocation_attribute_type__name="service_rate_category", allocationattribute__value="subscription").values("pk")
        consumption_allocations = Allocation.objects.filter(allocationattribute__allocation_attribute_type__name="service_rate_category", allocationattribute__value="consumption").values("pk")
        
        self.assertEqual(subscription_allocations.count(), 0)
        self.assertEqual(consumption_allocations.count(), 2)