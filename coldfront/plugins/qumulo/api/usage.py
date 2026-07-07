from datetime import date, datetime, timedelta

from django.http import (
    JsonResponse,
    HttpRequest,
    HttpResponseBadRequest,
    HttpResponseNotFound,
)
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.context_processors import auth

from coldfront.core.allocation.models import Allocation, AllocationAttributeUsage

from pprint import pprint

EOD = "T23:59:59+00:00"


class AccessMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        pprint(request.user)
        pprint(auth(request))
        return super().dispatch(request, *args, **kwargs)


class Usage(AccessMixin, View):
    # queryparams: allocation_id, startdate, end_date
    def get(self, request: HttpRequest, *args, **kwargs):
        allocation_id_str = request.GET.get("allocation_id", "")
        start_date_str = request.GET.get("start_date", "")
        end_date_str = request.GET.get("end_date", date.today().isoformat())

        end_datetime = datetime.fromisoformat(end_date_str + EOD)

        if start_date_str != "":
            start_datetime = datetime.fromisoformat(start_date_str + EOD)
        else:
            start_datetime = end_datetime - timedelta(days=365)
            start_datetime.replace(day=1)

        if start_datetime > end_datetime:
            return HttpResponseBadRequest(
                content="end_date must be later than start_date"
            )

        allocation_id = int(allocation_id_str)

        try:
            allocation = Allocation.objects.get(pk=allocation_id)
        except Allocation.DoesNotExist:
            return HttpResponseNotFound("allocation not found")
        quota_gib: int = allocation.get_attribute("storage_quota") * 2**10

        usage_gib = []
        end_date_usage: AllocationAttributeUsage = (
            AllocationAttributeUsage.history.as_of(end_datetime)
            .filter(
                allocation_attribute__allocation=allocation,
                allocation_attribute__allocation_attribute_type__name="storage_quota",
            )
            .first()
        )
        usage_gib.append({"date": end_date_str, "usage": end_date_usage.value / 2**30})

        i = 0
        working_datetime = end_datetime
        while working_datetime > start_datetime:
            working_datetime = _minus_months(end_datetime, i)

            if working_datetime == end_datetime:
                i = i + 1
                continue  # avoids issues when run on 1st of month

            if isinstance(start_datetime, date) and start_datetime > working_datetime:
                working_datetime = start_datetime

            working_usage: AllocationAttributeUsage = (
                AllocationAttributeUsage.history.as_of(working_datetime)
                .filter(
                    allocation_attribute__allocation=allocation,
                    allocation_attribute__allocation_attribute_type__name="storage_quota",
                )
                .first()
            )

            if working_usage != None:
                usage_gib.insert(
                    0,
                    {
                        "date": working_datetime.date().isoformat(),
                        "usage": working_usage.value / 2**30,
                    },
                )
            else:
                break

            i = i + 1

        return JsonResponse(
            {
                "allocation_id": allocation.pk,
                "quota": quota_gib,
                "usage": usage_gib,
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
