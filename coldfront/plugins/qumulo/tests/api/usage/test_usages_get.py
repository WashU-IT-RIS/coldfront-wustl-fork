from datetime import date, timedelta

from django.test import TestCase
from django.http import HttpRequest


from coldfront.plugins.qumulo.api.usage.usages import Usages
from coldfront.plugins.qumulo.tests.fixtures import (
    create_metadata_for_testing,
)
from coldfront.plugins.qumulo.tests.api.usage.helpers import (
    create_allocation_with_usage,
    create_usage_history,
    get_history_span,
)

import json

from freezegun import freeze_time


class TestUsageGet(TestCase):
    def setUp(self) -> None:
        create_metadata_for_testing()

        self.usage = Usages()

        self.request = HttpRequest()
        self.request.method = "GET"

        return super().setUp()

    def test_returns_latest_usage_for_specified_allocation(self) -> None:
        expected_quota_tib = 5
        expected_usage = 3.25 * 1024

        (storage_allocation, _) = create_allocation_with_usage(
            expected_quota_tib, expected_usage
        )

        self.request.GET.update({"allocation_id": storage_allocation.pk})
        response = self.usage.get(self.request)
        content = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(content["allocation_id"], storage_allocation.pk)
        self.assertListEqual(
            content["usage_data"],
            [
                {
                    "date": date.today().isoformat(),
                    "usage": expected_usage,
                    "quota": expected_quota_tib * 1024,
                }
            ],
        )

    def test_returns_usage_for_specific_date(self) -> None:
        current_quota_tib = 5
        expected_quota_tib = 3
        current_usage_gib = 3.25 * 1024
        expected_usage_gib = 2.6 * 1024
        specific_date = "2025-01-01"

        with freeze_time(date.fromisoformat(specific_date)):
            (storage_allocation, usage_object) = create_allocation_with_usage(
                expected_quota_tib, expected_usage_gib
            )

        usage_object.value = current_usage_gib * 2**30
        usage_object.save()

        quota_attribute = usage_object.allocation_attribute
        quota_attribute.value = current_quota_tib
        quota_attribute.save()

        self.request.GET.update(
            {"allocation_id": storage_allocation.pk, "end_date": specific_date}
        )
        response = self.usage.get(self.request)
        content = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(content["allocation_id"], storage_allocation.pk)
        self.assertEqual(content["usage_data"][0]["quota"], expected_quota_tib * 1024)
        self.assertEqual(content["usage_data"][0]["usage"], expected_usage_gib)

    def test_returns_monthly_list_by_year(self) -> None:
        current_quota_tib = 5
        current_usage_gib = 4.75 * 1024

        (storage_allocation, usage_object) = create_allocation_with_usage(
            current_quota_tib, current_usage_gib
        )

        usage_history = create_usage_history(usage_object, 12)
        usage_history.append(
            {
                "usage": current_usage_gib,
                "date": date.today().isoformat(),
                "quota": current_quota_tib * 2**10,
            }
        )

        self.request.GET.update({"allocation_id": storage_allocation.pk})
        response = self.usage.get(self.request)
        content = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(content["allocation_id"], storage_allocation.pk)
        self.assertIsInstance(content["usage_data"], list)
        self.assertEqual(len(content["usage_data"]), len(usage_history))
        self.assertListEqual(content["usage_data"], usage_history)

    def test_takes_in_start_time(self) -> None:
        current_quota_tib = 5
        current_usage_gib = 4 * 1024
        (storage_allocation, usage_object) = create_allocation_with_usage(
            current_quota_tib, current_usage_gib
        )

        usage_history = create_usage_history(usage_object, 12)
        usage_history.append(
            {
                "usage": current_usage_gib,
                "date": date.today().isoformat(),
                "quota": current_quota_tib * 2**10,
            }
        )

        (expected_history, start_date, _) = get_history_span(usage_history, 162)

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
        self.assertIsInstance(content["usage_data"], list)
        self.assertListEqual(content["usage_data"], expected_history)

    def test_checks_start_date_in_middle_of_the_month(self):
        expected_quota_tib = 4
        expected_usage_gib = 3.3 * 1024
        current_usage_gib = 4 * 1024
        current_quota_tib = 5

        (storage_allocation, usage_object) = create_allocation_with_usage(
            current_quota_tib, current_usage_gib
        )

        usage_history = create_usage_history(usage_object, 12)
        usage_history.append(
            {
                "usage": current_usage_gib,
                "date": date.today().isoformat(),
                "quota": current_quota_tib * 2**10,
            }
        )

        insert_month = 4

        expected_date = date.fromisoformat(
            usage_history[insert_month].get("date")
        ) + timedelta(days=15)
        usage_history.insert(
            insert_month + 1,
            {
                "usage": expected_usage_gib,
                "date": expected_date.isoformat(),
                "quota": expected_quota_tib * 2**10,
            },
        )

        with freeze_time(expected_date):
            quota_attribute = usage_object.allocation_attribute
            quota_attribute.value = expected_quota_tib
            quota_attribute.save()
            usage_object.value = expected_usage_gib * 2**30
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
        self.assertIsInstance(content["usage_data"], list)
        self.assertListEqual(content["usage_data"], expected_history)

    def test_returns_start_time_older_than_one_year(self):
        current_quota_tib = 5
        current_usage_gib = 4 * 1024
        (storage_allocation, usage_object) = create_allocation_with_usage(
            current_quota_tib, current_usage_gib
        )

        usage_history = create_usage_history(usage_object, 36)
        usage_history.append(
            {
                "usage": current_usage_gib,
                "date": date.today().isoformat(),
                "quota": current_quota_tib * 2**10,
            }
        )

        (expected_history, start_date, _) = get_history_span(usage_history, 400)

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
        self.assertIsInstance(content["usage_data"], list)
        self.assertListEqual(content["usage_data"], expected_history)

    def test_returns_expected_with_start_and_end(self):
        current_quota_tib = 5
        current_usage_gib = 4 * 1024
        (storage_allocation, usage_object) = create_allocation_with_usage(
            current_quota_tib, current_usage_gib
        )

        usage_history = create_usage_history(usage_object, 36)
        usage_history.append(
            {
                "usage": current_usage_gib,
                "date": date.today().isoformat(),
                "quota": current_quota_tib * 2**10,
            }
        )

        (expected_history, start_date, end_date) = get_history_span(
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
        self.assertIsInstance(content["usage_data"], list)
        self.assertListEqual(content["usage_data"], expected_history)

    def test_does_not_provide_data_that_exceeds_history(self):
        current_quota_tib = 5
        current_usage_gib = 4 * 1024
        (storage_allocation, usage_object) = create_allocation_with_usage(
            current_quota_tib, current_usage_gib
        )

        usage_history = create_usage_history(usage_object, 6)
        usage_history.append(
            {
                "usage": current_usage_gib,
                "date": date.today().isoformat(),
                "quota": current_quota_tib * 2**10,
            }
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
        self.assertIsInstance(content["usage_data"], list)
        self.assertListEqual(content["usage_data"], expected_history)

    def test_returns_error_when_start_date_is_after_end_date(self):
        current_quota_tib = 5
        current_usage_gib = 4 * 1024
        (storage_allocation, usage_object) = create_allocation_with_usage(
            current_quota_tib, current_usage_gib
        )

        usage_history = create_usage_history(usage_object, 36)
        usage_history.append(
            {
                "usage": current_usage_gib,
                "date": date.today().isoformat(),
                "quota": current_quota_tib * 2**10,
            }
        )

        (expected_history, start_date, end_date) = get_history_span(
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
