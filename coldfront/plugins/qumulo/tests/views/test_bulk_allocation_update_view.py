import json
from unittest.mock import patch

from django.test import RequestFactory, TestCase

from coldfront.core.allocation.models import (
    AllocationAttributeChangeRequest,
    AllocationChangeRequest,
)
from coldfront.core.test_helpers.factories import (
    AAttributeTypeFactory,
    AllocationAttributeFactory,
    AllocationAttributeTypeFactory,
    AllocationChangeStatusChoiceFactory,
    AllocationFactory,
    ResourceFactory,
    UserFactory,
)
from coldfront.plugins.qumulo.views.bulk_suballocation_update_view import (
    BulkSubAllocationUpdateView,
)


class BulkAllocationUpdateViewTests(TestCase):
    def setUp(self):
        user_enrichment = patch(
            "coldfront.plugins.qumulo.signals.update_user_with_additional_data"
        )
        user_enrichment.start()
        self.addCleanup(user_enrichment.stop)
        self.user = UserFactory(username="admin_bulk_update", is_superuser=True)
        self.request_factory = RequestFactory()
        self.pending_status = AllocationChangeStatusChoiceFactory(name="Pending")
        resource = ResourceFactory(name="bulk-update-storage")
        self.attribute_type = AllocationAttributeTypeFactory(
            name="cost_center",
            attribute_type=AAttributeTypeFactory(name="Text"),
        )
        self.attributes = []
        for allocation in AllocationFactory.create_batch(3):
            allocation.resources.add(resource)
            self.attributes.append(
                AllocationAttributeFactory(
                    allocation=allocation,
                    allocation_attribute_type=self.attribute_type,
                    value="old-value",
                )
            )
        self.payload = {
            "attributeTypeId": self.attribute_type.pk,
            "value": "new-value",
            "allocationIds": [
                attribute.allocation_id for attribute in self.attributes[:2]
            ],
        }

    def post(self, payload):
        request = self.request_factory.post(
            "/qumulo/allocation-admin/bulk-suballocation-update",
            data=json.dumps(payload),
            content_type="application/json",
        )
        request.user = self.user
        return BulkSubAllocationUpdateView.as_view()(request)

    # Test that allocations are correctly updated in bulk
    def test_bulk_update_targets_only_selected_allocations(self):
        response = self.post(self.payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {"updatedAllocations": 2})
        self.assertCountEqual(
            AllocationChangeRequest.objects.values_list("allocation_id", flat=True),
            self.payload["allocationIds"],
        )
        for attribute in self.attributes:
            attribute.refresh_from_db()
            self.assertEqual(attribute.value, "old-value")
        self.assertFalse(
            AllocationAttributeChangeRequest.objects.filter(
                allocation_attribute=self.attributes[2]
            ).exists()
        )

    # Test that change requests are correctly created for updated allocations
    def test_bulk_update_creates_pending_change_requests(self):
        response = self.post(self.payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(AllocationChangeRequest.objects.count(), 2)
        self.assertEqual(AllocationAttributeChangeRequest.objects.count(), 2)
        for attribute in self.attributes[:2]:
            change = AllocationAttributeChangeRequest.objects.get(
                allocation_attribute=attribute
            )
            self.assertEqual(change.new_value, "new-value")
            parent = change.allocation_change_request
            self.assertEqual(parent.allocation_id, attribute.allocation_id)
            self.assertEqual(parent.status, self.pending_status)
            self.assertEqual(parent.user, self.user)

    # Test that the view handles invalid form submissions correctly
    def test_invalid_form_submission_does_not_create_changes(self):
        response = self.post({**self.payload, "value": ""})

        self.assertEqual(response.status_code, 400)
        self.assertIn("value:", json.loads(response.content)["error"])
        self.assertFalse(AllocationChangeRequest.objects.exists())
        self.assertFalse(AllocationAttributeChangeRequest.objects.exists())
        for attribute in self.attributes:
            attribute.refresh_from_db()
            self.assertEqual(attribute.value, "old-value")