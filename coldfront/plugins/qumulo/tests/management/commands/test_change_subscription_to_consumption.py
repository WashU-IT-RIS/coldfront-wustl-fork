from django.test import TestCase, Client

from coldfront.plugins.qumulo.tests.utils.mock_data import (
    build_models,
    default_form_data,
    create_allocation,
)
from coldfront.core.allocation.models import Allocation, AllocationStatusChoice

from django.core.management import call_command


class TestChangeSubscriptionToConsumption(TestCase):
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
        non_subscription_allocation = create_allocation(
            self.project, self.user, self.no_subscription_form_data
        )
        subscription_allocation = create_allocation(
            self.project, self.user, self.subscription_form_data
        )
        subscription_allocation.status = AllocationStatusChoice.objects.get(
            name="Active"
        )
        subscription_allocation.save()
        non_subscription_allocation.status = AllocationStatusChoice.objects.get(
            name="Active"
        )
        non_subscription_allocation.save()

        subscription_allocations = Allocation.objects.filter(
            allocationattribute__allocation_attribute_type__name="service_rate_category",
            allocationattribute__value="subscription",
        )
        self.assertEqual(subscription_allocations.count(), 1)

        call_command("change_subscription_to_consumption")

        subscription_allocations = Allocation.objects.filter(
            allocationattribute__allocation_attribute_type__name="service_rate_category",
            allocationattribute__value="subscription",
        )
        consumption_allocations = Allocation.objects.filter(
            allocationattribute__allocation_attribute_type__name="service_rate_category",
            allocationattribute__value="consumption",
        )

        self.assertEqual(subscription_allocations.count(), 0)
        self.assertEqual(consumption_allocations.count(), 2)

    def test_no_subscription_allocations(self):
        allocation_one = create_allocation(
            self.project, self.user, self.no_subscription_form_data
        )
        allocation_two = create_allocation(
            self.project, self.user, self.no_subscription_form_data
        )
        allocation_one.status = AllocationStatusChoice.objects.get(name="Active")
        allocation_one.save()
        allocation_two.status = AllocationStatusChoice.objects.get(name="Active")
        allocation_two.save()

        call_command("change_subscription_to_consumption")

        subscription_allocations = Allocation.objects.filter(
            allocationattribute__allocation_attribute_type__name="service_rate_category",
            allocationattribute__value="subscription",
        )
        consumption_allocations = Allocation.objects.filter(
            allocationattribute__allocation_attribute_type__name="service_rate_category",
            allocationattribute__value="consumption",
        )

        self.assertEqual(subscription_allocations.count(), 0)
        self.assertEqual(consumption_allocations.count(), 2)

    def test_deleted_subscription_allocation(self):
        non_subscription_allocation = create_allocation(
            self.project, self.user, self.no_subscription_form_data
        )
        subscription_allocation = create_allocation(
            self.project, self.user, self.subscription_form_data
        )
        deleted_subscription_allocation = create_allocation(
            self.project, self.user, self.subscription_form_data
        )

        subscription_allocation.status = AllocationStatusChoice.objects.get(
            name="Active"
        )
        subscription_allocation.save()
        non_subscription_allocation.status = AllocationStatusChoice.objects.get(
            name="Active"
        )
        non_subscription_allocation.save()
        deleted_subscription_allocation.status = AllocationStatusChoice.objects.get(
            name="Deleted"
        )
        deleted_subscription_allocation.save()

        subscription_allocations = Allocation.objects.filter(
            allocationattribute__allocation_attribute_type__name="service_rate_category",
            allocationattribute__value="subscription",
        )
        self.assertEqual(subscription_allocations.count(), 2)

        call_command("change_subscription_to_consumption")

        subscription_allocations = Allocation.objects.filter(
            allocationattribute__allocation_attribute_type__name="service_rate_category",
            allocationattribute__value="subscription",
        )
        consumption_allocations = Allocation.objects.filter(
            allocationattribute__allocation_attribute_type__name="service_rate_category",
            allocationattribute__value="consumption",
        )

        self.assertEqual(subscription_allocations.count(), 1)
        self.assertEqual(consumption_allocations.count(), 2)
