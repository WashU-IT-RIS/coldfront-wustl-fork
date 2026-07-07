from datetime import date, datetime, timedelta
from random import random

from typing import Tuple

from django.test import TestCase
from django.http import HttpRequest

from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttribute,
    AllocationAttributeUsage,
)
from coldfront.core.test_helpers.factories import AllocationAttributeUsageFactory

from coldfront.plugins.qumulo.api.usage import Usage
from coldfront.plugins.qumulo.tests.fixtures import (
    create_metadata_for_testing,
    create_ris_project_and_allocations_storage3,
)

import json


def _create_allocation_with_usage(
    quota_tib: int = 5, usage_gib: float = 3.25
) -> Tuple[Allocation, AllocationAttributeUsage]:
    _, allocations = create_ris_project_and_allocations_storage3(
        storage_filesystem_path="/storage3/fs1/testuser",
    )
    storage_allocation = allocations["storage_allocation"]
    storage_quota = AllocationAttribute.objects.get(
        allocation=storage_allocation, allocation_attribute_type__name="storage_quota"
    )

    storage_quota.value = quota_tib
    storage_quota.save()

    quota_usage: AllocationAttributeUsage = AllocationAttributeUsageFactory(
        allocation_attribute=allocations[
            "storage_allocation"
        ].allocationattribute_set.get(allocation_attribute_type__name="storage_quota"),
        value=usage_gib * 2**30,
    )

    return (storage_allocation, quota_usage)


def _create_usage_history(
    usage_object: AllocationAttributeUsage, months: int = 12, max_usage: int = 5
) -> list[dict]:
    usage_history = []
    today = date.today()

    for i in range(months):
        current_month = today.month
        new_month = current_month - i

        working_date = today.replace(day=1)
        while new_month <= 0:
            new_month = new_month + 12
            working_date = working_date.replace(year=working_date.year - 1)
        working_date = working_date.replace(month=new_month)

        if working_date == today:
            continue  # avoids issues when run on 1st of month

        usage_tib = round(random() * max_usage, 12)

        usage_history.insert(
            0, {"usage": usage_tib * 2**10, "date": working_date.isoformat()}
        )

        usage_object.value = usage_tib * 2**40
        usage_object._history_date = datetime.fromisoformat(
            working_date.isoformat() + "T00:00:00+00:00"
        )
        usage_object.save()

    return usage_history


def _get_history_span(
    usage_history: list[dict], start_day_delta: int, end_day_delta: int = 0
):
    start_date = date.today() - timedelta(days=start_day_delta)
    end_date = date.today() - timedelta(days=end_day_delta)

    working_history = []
    has_succeeded = False
    for index, history in enumerate(usage_history):
        history_date = date.fromisoformat(history["date"])
        if history_date >= start_date and history_date <= end_date:
            if not has_succeeded:
                working_history.append(
                    {
                        "date": start_date.isoformat(),
                        "usage": usage_history[index - 1]["usage"],
                    }
                )
                has_succeeded = True
            working_history.append(history)

    if working_history[-1]["date"] != end_date.isoformat():
        working_history.append(
            {"date": end_date.isoformat(), "usage": working_history[-1]["usage"]}
        )

    return (working_history, start_date, end_date)


class TestUsageGet(TestCase):
    def setUp(self) -> None:
        create_metadata_for_testing()

        self.usage = Usage()

        self.request = HttpRequest()
        self.request.method = "GET"

        return super().setUp()

    def test_returns_latest_usage_for_specified_allocation(self) -> None:
        expected_quota_tib = 5
        expected_usage = 3.25 * 1024

        (storage_allocation, _) = _create_allocation_with_usage(
            expected_quota_tib, expected_usage
        )

        self.request.GET.update({"allocation_id": storage_allocation.pk})
        response = self.usage.get(self.request)
        content = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(content["allocation_id"], storage_allocation.pk)
        self.assertEqual(content["quota"], expected_quota_tib * 1024)
        self.assertListEqual(
            content["usage"],
            [{"date": date.today().isoformat(), "usage": expected_usage}],
        )

    def test_returns_usage_for_specific_date(self) -> None:
        expected_quota_tib = 5
        current_usage_gib = 3.25 * 1024
        expected_usage_gib = 2.6 * 1024
        specific_date = "2025-01-01"

        (storage_allocation, usage_object) = _create_allocation_with_usage(
            expected_quota_tib, current_usage_gib
        )

        usage_object.value = expected_usage_gib * 2**30
        usage_object._history_date = datetime.fromisoformat(
            specific_date + "T00:00:00+00:00"
        )
        usage_object.save()

        self.request.GET.update(
            {"allocation_id": storage_allocation.pk, "end_date": specific_date}
        )
        response = self.usage.get(self.request)
        content = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(content["allocation_id"], storage_allocation.pk)
        self.assertEqual(content["quota"], expected_quota_tib * 1024)
        self.assertEqual(content["usage"][0]["usage"], expected_usage_gib)

    def test_returns_monthly_list_by_year(self) -> None:
        expected_quota_tib = 5
        current_usage_gib = 4.75 * 1024

        (storage_allocation, usage_object) = _create_allocation_with_usage(
            expected_quota_tib, current_usage_gib
        )

        usage_history = _create_usage_history(usage_object, 12, expected_quota_tib)
        usage_history.append(
            {"usage": current_usage_gib, "date": date.today().isoformat()}
        )

        self.request.GET.update({"allocation_id": storage_allocation.pk})
        response = self.usage.get(self.request)
        content = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(content["allocation_id"], storage_allocation.pk)
        self.assertEqual(content["quota"], expected_quota_tib * 1024)
        self.assertIsInstance(content["usage"], list)
        self.assertListEqual(content["usage"], usage_history)

    def test_takes_in_start_time(self) -> None:
        expected_quota_tib = 5
        current_usage_gib = 4 * 1024
        (storage_allocation, usage_object) = _create_allocation_with_usage(
            expected_quota_tib, current_usage_gib
        )

        usage_history = _create_usage_history(usage_object, 12, expected_quota_tib)
        usage_history.append(
            {"usage": current_usage_gib, "date": date.today().isoformat()}
        )

        (expected_history, start_date, _) = _get_history_span(usage_history, 162)

        self.request.GET.update(
            {
                "allocation_id": storage_allocation.pk,
                "start_date": start_date.isoformat(),
            }
        )
        response = self.usage.get(self.request)
        content = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(content["allocation_id"], storage_allocation.pk)
        self.assertEqual(content["quota"], expected_quota_tib * 1024)
        self.assertIsInstance(content["usage"], list)
        self.assertListEqual(content["usage"], expected_history)

    def test_checks_start_date_in_middle_of_the_month(self):
        expected_quota_tib = 5
        expected_usage_gib = 3.3 * 1024
        current_usage_gib = 4 * 1024
        (storage_allocation, usage_object) = _create_allocation_with_usage(
            expected_quota_tib, current_usage_gib
        )

        usage_history = _create_usage_history(usage_object, 12, expected_quota_tib)
        usage_history.append(
            {"usage": current_usage_gib, "date": date.today().isoformat()}
        )

        insert_month = 4

        expected_date = date.fromisoformat(
            usage_history[insert_month].get("date")
        ) + timedelta(days=15)
        usage_history.insert(
            insert_month + 1,
            {"usage": expected_usage_gib, "date": expected_date.isoformat()},
        )

        usage_object.value = expected_usage_gib * 2**30
        usage_object._history_date = datetime.fromisoformat(
            expected_date.isoformat() + "T00:00:00+00:00"
        )
        usage_object.save()

        start_date = expected_date
        expected_history = list(
            filter(
                lambda item: date.fromisoformat(item["date"]) >= start_date,
                usage_history,
            )
        )

        self.request.GET.update(
            {
                "allocation_id": storage_allocation.pk,
                "start_date": expected_date.isoformat(),
            }
        )
        response = self.usage.get(self.request)
        content = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(content["allocation_id"], storage_allocation.pk)
        self.assertEqual(content["quota"], expected_quota_tib * 1024)
        self.assertIsInstance(content["usage"], list)
        self.assertListEqual(content["usage"], expected_history)

    def test_returns_start_time_older_than_one_year(self):
        expected_quota_tib = 5
        current_usage_gib = 4 * 1024
        (storage_allocation, usage_object) = _create_allocation_with_usage(
            expected_quota_tib, current_usage_gib
        )

        usage_history = _create_usage_history(usage_object, 36, expected_quota_tib)
        usage_history.append(
            {"usage": current_usage_gib, "date": date.today().isoformat()}
        )

        (expected_history, start_date, _) = _get_history_span(usage_history, 400)

        self.request.GET.update(
            {
                "allocation_id": storage_allocation.pk,
                "start_date": start_date.isoformat(),
            }
        )
        response = self.usage.get(self.request)
        content = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(content["allocation_id"], storage_allocation.pk)
        self.assertEqual(content["quota"], expected_quota_tib * 1024)
        self.assertIsInstance(content["usage"], list)
        self.assertListEqual(content["usage"], expected_history)

    def test_returns_expected_with_start_and_end(self):
        expected_quota_tib = 5
        current_usage_gib = 4 * 1024
        (storage_allocation, usage_object) = _create_allocation_with_usage(
            expected_quota_tib, current_usage_gib
        )

        usage_history = _create_usage_history(usage_object, 36, expected_quota_tib)
        usage_history.append(
            {"usage": current_usage_gib, "date": date.today().isoformat()}
        )

        (expected_history, start_date, end_date) = _get_history_span(
            usage_history, 365, 180
        )

        self.request.GET.update(
            {
                "allocation_id": storage_allocation.pk,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            }
        )
        response = self.usage.get(self.request)
        content = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(content["allocation_id"], storage_allocation.pk)
        self.assertEqual(content["quota"], expected_quota_tib * 1024)
        self.assertIsInstance(content["usage"], list)
        self.assertListEqual(content["usage"], expected_history)

    def test_does_not_provide_data_that_exceeds_history(self):
        expected_quota_tib = 5
        current_usage_gib = 4 * 1024
        (storage_allocation, usage_object) = _create_allocation_with_usage(
            expected_quota_tib, current_usage_gib
        )

        usage_history = _create_usage_history(usage_object, 6, expected_quota_tib)
        usage_history.append(
            {"usage": current_usage_gib, "date": date.today().isoformat()}
        )

        expected_history = usage_history
        start_date = date.fromisoformat(expected_history[0]["date"]) - timedelta(
            days=365
        )

        self.request.GET.update(
            {
                "allocation_id": storage_allocation.pk,
                "start_date": start_date.isoformat(),
            }
        )
        response = self.usage.get(self.request)
        content = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(content["allocation_id"], storage_allocation.pk)
        self.assertEqual(content["quota"], expected_quota_tib * 1024)
        self.assertIsInstance(content["usage"], list)
        self.assertListEqual(content["usage"], expected_history)

    def test_returns_error_when_start_date_is_after_end_date(self):
        expected_quota_tib = 5
        current_usage_gib = 4 * 1024
        (storage_allocation, usage_object) = _create_allocation_with_usage(
            expected_quota_tib, current_usage_gib
        )

        usage_history = _create_usage_history(usage_object, 36, expected_quota_tib)
        usage_history.append(
            {"usage": current_usage_gib, "date": date.today().isoformat()}
        )

        (expected_history, start_date, end_date) = _get_history_span(
            usage_history, 365, 180
        )

        self.request.GET.update(
            {
                "allocation_id": storage_allocation.pk,
                "start_date": end_date.isoformat(),
                "end_date": start_date.isoformat(),
            }
        )
        response = self.usage.get(self.request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.content.decode(), "end_date must be later than start_date"
        )

    def test_returns_404_with_bad_allocation(self):
        self.request.GET.update(
            {
                "allocation_id": 100,
            }
        )
        response = self.usage.get(self.request)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content.decode(), "allocation not found")
