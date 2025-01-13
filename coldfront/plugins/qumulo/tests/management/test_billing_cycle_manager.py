from django.test import TestCase, Client

from unittest.mock import patch

from unittest import skip

from django.db.models import OuterRef, Subquery

from coldfront.plugins.qumulo.tests.utils.mock_data import (
    build_models,
    create_allocation,
)

import logging
from coldfront.core.allocation.models import (
    AllocationAttributeType,
    AllocationAttribute,
)
from datetime import datetime

from coldfront.plugins.qumulo.management.commands.check_billing_cycles import (
    calculate_prepaid_expiration,
    process_prepaid_billing_cycle_changes,
)

logger = logging.getLogger(__name__)


class TestBillingCycleTypeUpdates(TestCase):
    def setUp(self):
        self.client = Client()
        build_data = build_models()

        self.project = build_data["project"]
        self.user = build_data["user"]
        self.prepaid_past_form_data = {
            "storage_filesystem_path": "foo",
            "storage_export_path": "bar",
            "storage_ticket": "ITSD-54321",
            "storage_name": "baz",
            "storage_quota": 7,
            "protocols": ["nfs"],
            "rw_users": ["test"],
            "ro_users": ["test1"],
            "cost_center": "Uncle Pennybags",
            "department_number": "Time Travel Services",
            "service_rate": "general",
            "billing_cycle": "prepaid",
            "prepaid_time": 6,
            "prepaid_billing_date": "2024-11-01",
        }
        self.prepaid_present_form_data = {
            "storage_filesystem_path": "foo",
            "storage_export_path": "bar",
            "storage_ticket": "ITSD-54321",
            "storage_name": "baz",
            "storage_quota": 7,
            "protocols": ["nfs"],
            "rw_users": ["test"],
            "ro_users": ["test1"],
            "cost_center": "Uncle Pennybags",
            "department_number": "Time Travel Services",
            "service_rate": "general",
            "billing_cycle": "monthly",
            "prepaid_time": 3,
            "prepaid_billing_date": datetime.today().strftime("%Y-%m-%d"),
        }

    def prepaid_expiration_calculation_for_comparison(
        allocation, prepaid_billing_start, prepaid_months
    ):
        prepaid_billing_start = datetime.strptime(prepaid_billing_start, "%Y-%m-%d")
        prepaid_until = datetime(
            prepaid_billing_start.year
            + (prepaid_billing_start.month + prepaid_months - 1) // 12,
            (prepaid_billing_start.month + prepaid_months - 1) % 12 + 1,
            prepaid_billing_start.day,
        )

        return prepaid_until

    def test_prepaid_past_expiration_date(self):
        allocation = create_allocation(
            self.project, self.user, self.prepaid_past_form_data
        )

        prepaid_billing_start = self.prepaid_past_form_data["prepaid_billing_date"]
        prepaid_months = self.prepaid_past_form_data["prepaid_time"]

        calculate_prepaid_expiration(
            allocation,
            self.prepaid_past_form_data["billing_cycle"],
            prepaid_months,
            str(prepaid_billing_start),
            None,
        )
        prepaid_expiration_attribute = AllocationAttributeType.objects.get(
            name="prepaid_expiration"
        )
        prepaid_exp_value = AllocationAttribute.objects.get(
            allocation=allocation,
            allocation_attribute_type=prepaid_expiration_attribute,
        ).value
        prepaid_until = (
            TestBillingCycleTypeUpdates.prepaid_expiration_calculation_for_comparison(
                allocation, prepaid_billing_start, prepaid_months
            )
        )

        self.assertEqual(prepaid_exp_value, str(prepaid_until))

    def test_prepaid_present_expiration_date(self):
        allocation = create_allocation(
            self.project, self.user, self.prepaid_present_form_data
        )

        prepaid_billing_start = self.prepaid_past_form_data["prepaid_billing_date"]
        prepaid_months = self.prepaid_past_form_data["prepaid_time"]

        calculate_prepaid_expiration(
            allocation,
            self.prepaid_past_form_data["billing_cycle"],
            prepaid_months,
            str(prepaid_billing_start),
            None,
        )
        prepaid_expiration_attribute = AllocationAttributeType.objects.get(
            name="prepaid_expiration"
        )
        prepaid_exp_value = AllocationAttribute.objects.get(
            allocation=allocation,
            allocation_attribute_type=prepaid_expiration_attribute,
        ).value
        prepaid_until = (
            TestBillingCycleTypeUpdates.prepaid_expiration_calculation_for_comparison(
                allocation, prepaid_billing_start, prepaid_months
            )
        )
        self.assertEqual(prepaid_exp_value, str(prepaid_until))

    def test_prepaid_start_today(self) -> None:
        allocation = create_allocation(
            self.project, self.user, self.prepaid_present_form_data
        )
        billing_cycle_attribute = AllocationAttributeType.objects.get(
            name="billing_cycle"
        )
        prepaid_expiration_attribute = AllocationAttributeType.objects.get(
            name="prepaid_expiration"
        )
        AllocationAttribute.objects.get_or_create(
            allocation_attribute_type=prepaid_expiration_attribute,
            allocation=allocation,
            value="2025-06-02",
        )
        prepaid_exp = allocation.get_attribute(name="prepaid_expiration")

        process_prepaid_billing_cycle_changes(
            allocation,
            billing_cycle_attribute,
            self.prepaid_present_form_data["billing_cycle"],
            self.prepaid_present_form_data["prepaid_billing_date"],
            prepaid_exp,
        )
        final_bill_cycle = allocation.get_attribute(name="billing_cycle")
        final_service_rate = allocation.get_attribute(name="service_rate")
        self.assertEqual(final_bill_cycle, "prepaid")
        self.assertEqual(final_service_rate, "subscription")

    def test_monthly_start_today(self) -> None:
        allocation = create_allocation(
            self.project, self.user, self.prepaid_past_form_data
        )
        billing_cycle_attribute = AllocationAttributeType.objects.get(
            name="billing_cycle"
        )
        prepaid_expiration_attribute = AllocationAttributeType.objects.get(
            name="prepaid_expiration"
        )
        AllocationAttribute.objects.get_or_create(
            allocation_attribute_type=prepaid_expiration_attribute,
            allocation=allocation,
            value=datetime.today().strftime("%Y-%m-%d"),
        )
        prepaid_exp = allocation.get_attribute(name="prepaid_expiration")

        process_prepaid_billing_cycle_changes(
            allocation,
            billing_cycle_attribute,
            self.prepaid_past_form_data["billing_cycle"],
            self.prepaid_past_form_data["prepaid_billing_date"],
            prepaid_exp,
        )
        final_bill_cycle = allocation.get_attribute(name="billing_cycle")
        self.assertEqual(final_bill_cycle, "monthly")
