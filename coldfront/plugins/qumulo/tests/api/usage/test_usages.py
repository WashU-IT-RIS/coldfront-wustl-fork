from django.test import TestCase

from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttribute,
)
from coldfront.core.user.models import User
from coldfront.core.test_helpers.factories import (
    UserFactory,
    AllocationAttributeFactory,
)

from coldfront.plugins.qumulo.tests.fixtures import (
    create_metadata_for_testing,
)
from coldfront.plugins.qumulo.tests.api.usage.helpers import (
    create_allocation_with_usage,
)


class TestUsage(TestCase):
    def setUp(self):
        create_metadata_for_testing()

        self.expected_quota_tib = 5
        self.expected_usage = 3.25 * 1024

        (storage_allocation, _) = create_allocation_with_usage(
            self.expected_quota_tib, self.expected_usage
        )
        self.storage_allocation_pk = storage_allocation.pk

        return super().setUp()

    def test_restricts_anonymous_users(self):
        response = self.client.get(
            "/qumulo/api/usages", {"allocation_id": self.storage_allocation_pk}
        )

        self.assertEqual(response.status_code, 302)

    def test_restricts_basic_users(self):
        basic_user = UserFactory.create()

        self.client.force_login(basic_user)
        response = self.client.get(
            "/qumulo/api/usages", {"allocation_id": self.storage_allocation_pk}
        )

        self.assertEqual(response.status_code, 403)

    def test_allows_admin(self):
        user = UserFactory.create(is_superuser=True)

        self.client.force_login(user)
        response = self.client.get(
            "/qumulo/api/usages", {"allocation_id": self.storage_allocation_pk}
        )

        self.assertEqual(response.status_code, 200)

    def test_allows_staff(self):
        user = UserFactory.create(is_staff=True)

        self.client.force_login(user)
        response = self.client.get(
            "/qumulo/api/usages", {"allocation_id": self.storage_allocation_pk}
        )

        self.assertEqual(response.status_code, 200)

    def test_allows_pi(self):
        pi = Allocation.objects.get(pk=self.storage_allocation_pk).project.pi

        self.client.force_login(pi)
        response = self.client.get(
            "/qumulo/api/usages", {"allocation_id": self.storage_allocation_pk}
        )

        self.assertEqual(response.status_code, 200)

    def test_allows_billing_contact(self):
        billing_user: User = UserFactory.create()

        billing_contact_attribute = AllocationAttribute.objects.get(
            allocation__pk=self.storage_allocation_pk,
            allocation_attribute_type__name="billing_contact",
        )
        billing_contact_attribute.value = billing_user.username
        billing_contact_attribute.save()

        self.client.force_login(billing_user)
        response = self.client.get(
            "/qumulo/api/usages", {"allocation_id": self.storage_allocation_pk}
        )

        self.assertEqual(response.status_code, 200)

    def test_allows_technical_contact(self):
        technical_user: User = UserFactory.create()

        AllocationAttributeFactory(
            allocation=Allocation.objects.get(pk=self.storage_allocation_pk),
            allocation_attribute_type__name="technical_contact",
            value=technical_user.username,
        )

        self.client.force_login(technical_user)
        response = self.client.get(
            "/qumulo/api/usages", {"allocation_id": self.storage_allocation_pk}
        )

        self.assertEqual(response.status_code, 200)

    def test_works_with_no_billing_contact(self):
        pi = Allocation.objects.get(pk=self.storage_allocation_pk).project.pi

        billing_attribute = AllocationAttribute.objects.get(
            allocation__pk=self.storage_allocation_pk,
            allocation_attribute_type__name="billing_contact",
        )
        billing_attribute.delete()

        self.client.force_login(pi)
        response = self.client.get(
            "/qumulo/api/usages", {"allocation_id": self.storage_allocation_pk}
        )

        self.assertEqual(response.status_code, 200)
