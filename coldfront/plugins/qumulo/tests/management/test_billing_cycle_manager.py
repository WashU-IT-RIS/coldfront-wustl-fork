from django.test import TestCase, Client

from unittest.mock import patch, MagicMock

from unittest import skip

from django.db.models import OuterRef, Subquery

from coldfront.plugins.qumulo.utils.qumulo_api import QumuloAPI

from coldfront.plugins.qumulo.tests.utils.mock_data import (
    build_models,
    create_allocation,
)

from coldfront.core.allocation.signals import (
    allocation_activate,
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
    check_allocation_billing_cycle_and_prepaid_exp,
)

logger = logging.getLogger(__name__)


@patch("coldfront.plugins.qumulo.signals.QumuloAPI")
class TestBillingCycleTypeUpdates(TestCase):
    def mock_get_attribute(name):
        attribute_dict = {
            "storage_filesystem_path": "foo",
            "storage_export_path": "bar",
            "storage_name": "baz",
            "storage_quota": 7,
            "storage_protocols": '["nfs"]',
        }
        return attribute_dict[name]

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
            "prepaid_billing_date": "01-11-2024",
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

        self.client.force_login(self.user)

        self.prepaid_allocation = create_allocation(
            self.project, self.user, self.prepaid_past_form_data
        )

    @patch("coldfront.plugins.qumulo.signals.async_task")
    def test_billing_cycle_manager_end_to_end_past(
        self,
        mock_async_task: MagicMock,
        mock_QumuloAPI: MagicMock,
    ):
        qumulo_instance = mock_QumuloAPI.return_value
        breakpoint()
        allocation_activate.send(
            sender=self.__class__, allocation_pk=self.prepaid_allocation.pk
        )
        check_allocation_billing_cycle_and_prepaid_exp()
        return True

    # def prepaid_expiration_calculation_for_comparison(
    #     allocation, prepaid_billing_start, prepaid_months
    # ):
    #     prepaid_billing_start = datetime.strptime(prepaid_billing_start, "%Y-%m-%d")
    #     prepaid_until = datetime(
    #         prepaid_billing_start.year
    #         + (prepaid_billing_start.month + prepaid_months - 1) // 12,
    #         (prepaid_billing_start.month + prepaid_months - 1) % 12 + 1,
    #         prepaid_billing_start.day,
    #     )

    #     return prepaid_until

    # def billing_cycle_manager_prepaid_expiration_calculation(
    #     self, allocation, prepaid_months, prepaid_billing_start
    # ):
    #     calculate_prepaid_expiration(
    #         allocation,
    #         self.prepaid_past_form_data["billing_cycle"],
    #         prepaid_months,
    #         str(prepaid_billing_start),
    #         None,
    #     )
    #     prepaid_expiration_attribute = AllocationAttributeType.objects.get(
    #         name="prepaid_expiration"
    #     )
    #     prepaid_exp_value = AllocationAttribute.objects.get(
    #         allocation=allocation,
    #         allocation_attribute_type=prepaid_expiration_attribute,
    #     ).value
    #     return prepaid_exp_value

    # def test_prepaid_past_expiration_date(self):
    #     allocation = create_allocation(
    #         self.project, self.user, self.prepaid_past_form_data
    #     )
    #     breakpoint()

    #     prepaid_billing_start = self.prepaid_past_form_data["prepaid_billing_date"]
    #     prepaid_months = self.prepaid_past_form_data["prepaid_time"]

    #     prepaid_until = (
    #         TestBillingCycleTypeUpdates.prepaid_expiration_calculation_for_comparison(
    #             allocation, prepaid_billing_start, prepaid_months
    #         )
    #     )
    #     prepaid_exp_value = TestBillingCycleTypeUpdates.billing_cycle_manager_prepaid_expiration_calculation(
    #         self, allocation, prepaid_months, prepaid_billing_start
    #     )
    #     self.assertEqual(prepaid_exp_value, str(prepaid_until))

    # def test_prepaid_present_expiration_date(self):
    #     allocation = create_allocation(
    #         self.project, self.user, self.prepaid_present_form_data
    #     )
    #     breakpoint()
    #     prepaid_billing_start = self.prepaid_past_form_data["prepaid_billing_date"]
    #     prepaid_months = self.prepaid_past_form_data["prepaid_time"]

    #     prepaid_exp_value = TestBillingCycleTypeUpdates.billing_cycle_manager_prepaid_expiration_calculation(
    #         self, allocation, prepaid_months, prepaid_billing_start
    #     )
    #     prepaid_until = (
    #         TestBillingCycleTypeUpdates.prepaid_expiration_calculation_for_comparison(
    #             allocation, prepaid_billing_start, prepaid_months
    #         )
    #     )
    #     self.assertEqual(prepaid_exp_value, str(prepaid_until))

    # def test_prepaid_start_today(self) -> None:
    #     allocation = create_allocation(
    #         self.project, self.user, self.prepaid_present_form_data
    #     )
    #     billing_cycle_attribute = AllocationAttributeType.objects.get(
    #         name="billing_cycle"
    #     )
    #     prepaid_expiration_attribute = AllocationAttributeType.objects.get(
    #         name="prepaid_expiration"
    #     )
    #     AllocationAttribute.objects.get_or_create(
    #         allocation_attribute_type=prepaid_expiration_attribute,
    #         allocation=allocation,
    #         value="2025-06-02",
    #     )
    #     prepaid_exp = allocation.get_attribute(name="prepaid_expiration")

    #     process_prepaid_billing_cycle_changes(
    #         allocation,
    #         billing_cycle_attribute,
    #         self.prepaid_present_form_data["billing_cycle"],
    #         self.prepaid_present_form_data["prepaid_billing_date"],
    #         prepaid_exp,
    #     )
    #     final_bill_cycle = allocation.get_attribute(name="billing_cycle")
    #     final_service_rate = allocation.get_attribute(name="service_rate")
    #     self.assertEqual(final_bill_cycle, "prepaid")
    #     self.assertEqual(final_service_rate, "subscription")

    # def test_monthly_start_today(self) -> None:
    #     allocation = create_allocation(
    #         self.project, self.user, self.prepaid_past_form_data
    #     )
    #     billing_cycle_attribute = AllocationAttributeType.objects.get(
    #         name="billing_cycle"
    #     )
    #     prepaid_expiration_attribute = AllocationAttributeType.objects.get(
    #         name="prepaid_expiration"
    #     )
    #     AllocationAttribute.objects.get_or_create(
    #         allocation_attribute_type=prepaid_expiration_attribute,
    #         allocation=allocation,
    #         value=datetime.today().strftime("%Y-%m-%d"),
    #     )
    #     prepaid_exp = allocation.get_attribute(name="prepaid_expiration")

    #     process_prepaid_billing_cycle_changes(
    #         allocation,
    #         billing_cycle_attribute,
    #         self.prepaid_past_form_data["billing_cycle"],
    #         self.prepaid_past_form_data["prepaid_billing_date"],
    #         prepaid_exp,
    #     )
    #     final_bill_cycle = allocation.get_attribute(name="billing_cycle")
    #     self.assertEqual(final_bill_cycle, "monthly")
