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
    AllocationStatusChoice,
    AllocationAttributeType,
    AllocationAttribute,
)
from datetime import datetime, date

from coldfront.plugins.qumulo.management.commands.check_billing_cycles import (
    calculate_prepaid_expiration,
    process_prepaid_billing_cycle_changes,
    check_allocation_billing_cycle_and_prepaid_exp,
)

logger = logging.getLogger(__name__)


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
            "prepaid_billing_date": date(2024, 11, 1),
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
            "service_rate": "consumption",
            "billing_cycle": "monthly",
            "prepaid_time": 3,
            "prepaid_billing_date": date.today().strftime("%Y-%m-%d"),
        }
        self.prepaid_future_form_data = {
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
            "service_rate": "subscription",
            "billing_cycle": "monthly",
            "prepaid_time": 3,
            "prepaid_billing_date": date(2025, 11, 1),
        }
        self.monthly_form_data = {
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
            "service_rate": "subscription",
            "billing_cycle": "monthly",
        }

        self.client.force_login(self.user)

        self.prepaid_allocation = create_allocation(
            self.project, self.user, self.prepaid_past_form_data
        )
        self.prepaid_present_allocation = create_allocation(
            self.project, self.user, self.prepaid_present_form_data
        )
        self.prepaid_future_allocation = create_allocation(
            self.project, self.user, self.prepaid_future_form_data
        )
        self.monthly_allocation = create_allocation(
            self.project, self.user, self.monthly_form_data
        )

    def expected_prepaid_expiration_calculation(allocation):
        prepaid_months = AllocationAttribute.objects.get(
            allocation=allocation,
            allocation_attribute_type__name="prepaid_time",
        ).value

        prepaid_billing_start = AllocationAttribute.objects.get(
            allocation=allocation,
            allocation_attribute_type__name="prepaid_billing_date",
        ).value
        prepaid_billing_start = datetime.strptime(prepaid_billing_start, "%Y-%m-%d")
        prepaid_months = int(prepaid_months)

        prepaid_until = datetime(
            prepaid_billing_start.year
            + (prepaid_billing_start.month + prepaid_months - 1) // 12,
            (prepaid_billing_start.month + prepaid_months - 1) % 12 + 1,
            prepaid_billing_start.day,
        )

        return prepaid_until

    def test_billing_cycle_manager_past(self):
        self.prepaid_allocation.status = AllocationStatusChoice.objects.get(
            name="Active"
        )
        self.prepaid_allocation.save()

        check_allocation_billing_cycle_and_prepaid_exp()

        new_billing_cycle = AllocationAttribute.objects.get(
            allocation=self.prepaid_allocation,
            allocation_attribute_type__name="billing_cycle",
        ).value

        new_prepaid_expiration = AllocationAttribute.objects.get(
            allocation=self.prepaid_allocation,
            allocation_attribute_type__name="prepaid_expiration",
        ).value
        new_prepaid_expiration = datetime.strptime(
            new_prepaid_expiration, "%Y-%m-%d %H:%M:%S"
        )

        expected_prepaid_exp = (
            TestBillingCycleTypeUpdates.expected_prepaid_expiration_calculation(
                self.prepaid_allocation
            )
        )
        self.assertEqual(new_billing_cycle, "prepaid")
        self.assertEqual(new_prepaid_expiration, expected_prepaid_exp)

    def test_billing_cycle_manager_future(self):
        self.prepaid_future_allocation.status = AllocationStatusChoice.objects.get(
            name="Active"
        )
        self.prepaid_future_allocation.save()

        check_allocation_billing_cycle_and_prepaid_exp()

        new_billing_cycle = AllocationAttribute.objects.get(
            allocation=self.prepaid_future_allocation,
            allocation_attribute_type__name="billing_cycle",
        ).value

        self.assertEqual(new_billing_cycle, "monthly")

    def test_billing_cycle_manager_prepaid_today(self):
        self.prepaid_present_allocation.status = AllocationStatusChoice.objects.get(
            name="Active"
        )
        self.prepaid_present_allocation.save()

        check_allocation_billing_cycle_and_prepaid_exp()

        new_billing_cycle = AllocationAttribute.objects.get(
            allocation=self.prepaid_present_allocation,
            allocation_attribute_type__name="billing_cycle",
        ).value

        new_prepaid_expiration = AllocationAttribute.objects.get(
            allocation=self.prepaid_present_allocation,
            allocation_attribute_type__name="prepaid_expiration",
        ).value

        new_service_rate = AllocationAttribute.objects.get(
            allocation=self.prepaid_present_allocation,
            allocation_attribute_type__name="service_rate",
        ).value
        new_prepaid_expiration = datetime.strptime(
            new_prepaid_expiration, "%Y-%m-%d %H:%M:%S"
        )

        expected_prepaid_exp = (
            TestBillingCycleTypeUpdates.expected_prepaid_expiration_calculation(
                self.prepaid_present_allocation
            )
        )
        self.assertEqual(new_billing_cycle, "prepaid")
        self.assertEqual(new_service_rate, "subscription")
        self.assertEqual(new_prepaid_expiration, expected_prepaid_exp)

    def test_billing_cycle_manager_expires_today(self):
        self.prepaid_allocation.status = AllocationStatusChoice.objects.get(
            name="Active"
        )
        self.prepaid_allocation.save()

        prepaid_expiration_attribute = AllocationAttributeType.objects.get(
            name="prepaid_expiration"
        )

        AllocationAttribute.objects.create(
            allocation=self.prepaid_allocation,
            allocation_attribute_type=prepaid_expiration_attribute,
            value=date.today(),
        )

        check_allocation_billing_cycle_and_prepaid_exp()

        new_billing_cycle = AllocationAttribute.objects.get(
            allocation=self.prepaid_allocation,
            allocation_attribute_type__name="billing_cycle",
        ).value

        self.assertEqual(new_billing_cycle, "monthly")

    def test_billing_cycle_manager_monthly(self):
        self.monthly_allocation.status = AllocationStatusChoice.objects.get(
            name="Active"
        )
        self.monthly_allocation.save()

        check_allocation_billing_cycle_and_prepaid_exp()

        new_billing_cycle = AllocationAttribute.objects.get(
            allocation=self.monthly_allocation,
            allocation_attribute_type__name="billing_cycle",
        ).value

        self.assertEqual(new_billing_cycle, "monthly")
