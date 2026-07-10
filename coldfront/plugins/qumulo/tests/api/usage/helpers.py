from datetime import date, timedelta
from random import random

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
    usage_object: AllocationAttributeUsage, months: int = 12, max_usage: int = 5
) -> list[dict]:

    usage_history = []
    today = date.today()

    for month_offset in range(months):
        working_date = _adjust_month(today, month_offset)

        if working_date == today:
            continue  # avoids issues when run on 1st of month

        usage_tib = round(random() * max_usage, 12)

        usage_history.insert(
            0, {"usage": usage_tib * 2**10, "date": working_date.isoformat()}
        )

        with freeze_time(working_date):
            usage_object.value = usage_tib * 2**40
            usage_object.save()

    return usage_history


def _adjust_month(in_date: date, month_offset: int) -> date:
    current_month = in_date.month
    new_month = current_month - month_offset

    working_date = in_date.replace(day=1)
    while new_month <= 0:
        new_month = new_month + 12
        working_date = working_date.replace(year=working_date.year - 1)
    working_date = working_date.replace(month=new_month)

    return working_date


def get_history_span(
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
