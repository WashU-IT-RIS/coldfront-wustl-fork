from coldfront.core.allocation.models import Allocation

from django.test import TestCase

from coldfront.plugins.qumulo.tests.fixtures import (
    create_attribute_types_for_ris_allocations,
    create_ris_project_and_allocations_storage2,
    create_ris_project_and_allocations_storage3,
)


class TestAllocations(TestCase):

    def setUp(self) -> None:
        create_attribute_types_for_ris_allocations()
        path_storage2 = "/storage2/test/path"
        create_ris_project_and_allocations_storage2(path_storage2)
        path_storage3 = "/storage3/test/path"
        create_ris_project_and_allocations_storage3(path_storage3)
        return super().setUp()

    def test_active_storage_allocations_queryset(self):
        active_storage_allocations = Allocation.objects.active_storage()
        filtered_allocations = Allocation.objects.filter(
            status__name="Active", resources__resource_type__name="Storage"
        )
        self.assertQuerysetEqual(active_storage_allocations, filtered_allocations)

        should_contain_storage2_allocations = active_storage_allocations.filter(
            resources__name="Storage2"
        )
        self.assertTrue(should_contain_storage2_allocations.exists())

        should_contain_storage3_allocations = active_storage_allocations.filter(
            resources__name="Storage3"
        )
        self.assertTrue(should_contain_storage3_allocations.exists())

        should_contain_rw_allocations = active_storage_allocations.filter(
            resources__name="rw"
        )
        self.assertFalse(should_contain_rw_allocations.exists())

        should_contain_ro_allocations = active_storage_allocations.filter(
            resources__name="ro"
        )
        self.assertFalse(should_contain_ro_allocations.exists())

    def test_consumption_allocations_queryset(self):
        consumption_allocations = Allocation.objects.consumption()
        filtered_allocations = Allocation.objects.filter(
            allocationattribute__allocation_attribute_type__name="service_rate_category",
            allocationattribute__value="consumption",
        )
        self.assertQuerysetEqual(consumption_allocations, filtered_allocations)

    def test_parents_allocations_queryset(self):
        parents_allocations = Allocation.objects.parents()
        filtered_allocations = Allocation.objects.filter(parent_links=None)
        self.assertQuerysetEqual(parents_allocations, filtered_allocations)

    def test_parents_not_exempt(self):
        exempt_allocations = Allocation.objects.not_exempt()
        filtered_allocations = Allocation.objects.exclude(
            allocationattribute__allocation_attribute_type__name="billing_exempt",
            allocationattribute__value="yes",
        )
        self.assertQuerysetEqual(exempt_allocations, filtered_allocations)
        for allocation in exempt_allocations:
            exempt_attr = allocation.allocationattribute_set.filter(
                allocation_attribute_type__name="billing_exempt"
            ).first()
            self.assertNotEqual(exempt_attr.value, "yes") if exempt_attr else None
