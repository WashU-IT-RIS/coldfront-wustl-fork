from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from django.http import (
    JsonResponse,
    HttpRequest,
    HttpResponseBadRequest,
    HttpResponseNotFound,
)
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttributeUsage,
    AllocationAttribute,
)
from coldfront.core.user.models import User

from typing import Union, cast

EOD = "T23:59:59+00:00"


class Usages(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        user: User = self.request.user
        if user.is_superuser or user.is_staff:
            return True

        allocation_pk = int(self.request.GET.get("allocation_id"))
        allocation = Allocation.objects.get(pk=allocation_pk)
        pi_pk = allocation.project.pi.pk

        try:
            billing_contact_pk = User.objects.get(
                username=allocation.get_attribute("billing_contact")
            ).pk
        except User.DoesNotExist:
            billing_contact_pk = None

        try:
            technical_contact_pk = User.objects.get(
                username=allocation.get_attribute("technical_contact")
            ).pk
        except User.DoesNotExist:
            technical_contact_pk = None

        return (
            user.pk == pi_pk
            or user.pk == billing_contact_pk
            or user.pk == technical_contact_pk
        )

    # queryparams: allocation_id, startdate, end_date
    def get(self, request: HttpRequest, *args, **kwargs):
        allocation_id_str = request.GET.get("allocation_id", "")
        start_date_str = request.GET.get("start_date", "")
        end_date_str = request.GET.get("end_date", "")

        start_date = date.fromisoformat(start_date_str) if start_date_str else None
        end_date = date.fromisoformat(end_date_str) if end_date_str else None

        if (
            isinstance(start_date, date)
            and isinstance(end_date, date)
            and start_date > end_date
        ):
            return HttpResponseBadRequest(
                content="end_date must be later than start_date"
            )

        allocation_id = int(allocation_id_str)
        try:
            Allocation.objects.get(pk=allocation_id)
        except:
            return HttpResponseNotFound("allocation not found")

        quota_data = _get_quotas(allocation_id, start_date, end_date)
        usage_data = _get_usages_by_month(allocation_id, start_date, end_date)

        return JsonResponse(
            {
                "allocation_id": allocation_id,
                "usage_data": usage_data,
                "quota_data": quota_data,
            }
        )


def _minus_months(input_datetime: datetime, month_count: int) -> datetime:
    current_month = input_datetime.month
    new_month = current_month - month_count

    if new_month > 0:
        return_datetime = input_datetime.replace(day=1, month=new_month)
    else:
        new_month = current_month - month_count + 12
        return_datetime = input_datetime.replace(
            day=1, month=new_month, year=input_datetime.year - 1
        )

    return return_datetime


def _get_quotas(
    allocation_id: int,
    start_date: Union[date, None] = None,
    end_date: Union[date, None] = None,
) -> list:
    quota_attribute_history = AllocationAttribute.history.filter(
        allocation__pk=allocation_id,
        allocation_attribute_type__name="storage_quota",
    )

    if isinstance(start_date, date):
        next_date = start_date - relativedelta(days=1)

        quota_attribute_history = quota_attribute_history.filter(
            history_date__gt=next_date
        )
    if isinstance(end_date, date):
        quota_attribute_history = quota_attribute_history.filter(
            history_date__lte=end_date
        )

    history_iter = map(
        lambda element: {
            "quota": int(element.value) * 2**10,
            "date": element.history_date.date(),
        },
        quota_attribute_history,
    )
    history_iter = list(history_iter)
    if len(history_iter) > 1 and history_iter[0] == history_iter[1]:
        history_iter.pop(0)

    return history_iter


def _get_usages_by_month(
    allocation_id: int,
    start_date: Union[date, None] = None,
    end_date: Union[date, None] = None,
):
    usage_history = AllocationAttributeUsage.history.filter(
        allocation_attribute__allocation__pk=allocation_id,
        allocation_attribute__allocation_attribute_type__name="storage_quota",
    )

    if isinstance(start_date, date):
        usage_history = usage_history.filter(
            history_date__gt=start_date - relativedelta(days=1)
        )
    if isinstance(end_date, date):
        usage_history = usage_history.filter(
            history_date__lt=end_date + relativedelta(days=1)
        )

    history_iter = map(
        lambda element: {
            "usage": int(element.value) / 2**30,
            "date": element.history_date.date(),
        },
        usage_history,
    )
    history_iter = sorted(
        history_iter, key=lambda history: history.get("date"), reverse=True
    )

    first_element = history_iter[0]

    earliest_date: date = cast(date, history_iter[-1].get("date"))
    current_date: date = cast(date, first_element.get("date")).replace(day=1)

    working_list = []
    index = 0
    # go back month by month till we reach the beginning
    while current_date >= earliest_date:
        # go back in time till we are at or before the desired month
        while history_iter[index].get("date") > current_date:
            index = index + 1
            if index >= len(history_iter):
                break

        if index >= len(history_iter):
            break
        working_list.append(history_iter[index])
        current_date = current_date - relativedelta(months=1)

    if len(working_list) and working_list[-1].get("date") != earliest_date:
        working_list.append(history_iter[-1])

    history_iter = working_list

    if len(history_iter) == 0 or history_iter[0] != first_element:
        history_iter.insert(0, first_element)

    return history_iter
