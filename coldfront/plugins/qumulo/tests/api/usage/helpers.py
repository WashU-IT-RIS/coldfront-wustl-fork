from datetime import date
from dateutil.relativedelta import relativedelta
from random import random, randrange

from typing import Tuple

from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttribute,
    AllocationAttributeUsage,
)
from coldfront.core.test_helpers.factories import AllocationAttributeUsageFactory

from coldfront.plugins.qumulo.tests.fixtures import (
    create_ris_project_and_allocations_storage3,
)

from freezegun import freeze_time

from pprint import pprint


def create_allocation_with_usage(
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


def create_usage_history(
    usage_object: AllocationAttributeUsage, months: int = 12, max_usage_tib: int = 10
) -> Tuple:

    usage_data = []
    quota_data = []
    today = date.today()

    for month_offset in range(months):
        working_date = today - relativedelta(months=month_offset)

        if working_date == today:
            continue  # avoids issues when run on 1st of month

        quota_tib = round(random() * max_usage_tib)
        usage_kib = round(random() * quota_tib * 2**40)
        usage_tib = usage_kib / 2**40

        usage_data.insert(
            0,
            {
                "usage": usage_tib * 2**10,
                "date": working_date.isoformat(),
            },
        )
        quota_data.insert(
            0,
            {
                "quota": quota_tib * 2**10,
                "date": working_date.isoformat(),
            },
        )

        write_quota_history(
            usage_object.allocation_attribute.allocation.pk, working_date, quota_tib
        )
        write_usage_history(usage_object, working_date, usage_tib)

    return (usage_data, quota_data)


def get_history_span(history_data: dict, start_day_delta: int, end_day_delta: int = 0):
    start_date = date.today() - relativedelta(days=start_day_delta)
    end_date = date.today() - relativedelta(days=end_day_delta)

    working_history_data = {"usage_data": [], "quota_data": []}
    return_history_data = {"usage_data": [], "quota_data": []}

    for key in ["usage", "quota"]:
        data = history_data.get(f"{key}_data")
        working_data = working_history_data.get(f"{key}_data")

        has_succeeded = False
        for index, history in enumerate(data):
            history_date = date.fromisoformat(history["date"])
            if history_date >= start_date and history_date <= end_date:
                if not has_succeeded:
                    working_data.append(
                        {
                            "date": start_date.isoformat(),
                            key: data[index - 1].get(key),
                        }
                    )
                    has_succeeded = True
                working_data.append(history)

        if working_data[-1].get("date") != end_date.isoformat():
            working_data.append(
                {
                    "date": end_date.isoformat(),
                    key: working_data[-1].get(key),
                }
            )

        return_data = []
        for index, history in enumerate(working_data):
            if (
                index < len(working_data) - 1
                and history["date"] == working_data[index + 1]["date"]
            ):
                continue
            else:
                return_data.append(history)

        return_history_data[f"{key}_data"] = return_data

    return (
        {
            "usage_data": return_history_data["usage_data"],
            "quota_data": return_history_data["quota_data"],
        },
        start_date,
        end_date,
    )


def write_quota_history(allocation_id: int, this_date: date, quota_tib: int):
    with freeze_time(this_date):
        quota_attribute = AllocationAttribute.objects.get(
            allocation__pk=allocation_id,
            allocation_attribute_type__name="storage_quota",
        )
        quota_attribute.value = quota_tib
        quota_attribute.save()


def write_usage_history(
    usage_object: AllocationAttributeUsage, this_date: date, usage_tib: int
):
    with freeze_time(this_date):
        usage_object.value = usage_tib * 2**40
        usage_object.save()


def random_date(start: date, end: date):
    delta = end - start
    random_day = randrange(delta.days)

    return start + relativedelta(days=random_day)
