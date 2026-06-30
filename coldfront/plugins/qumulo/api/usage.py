from datetime import date, datetime

from django.http import JsonResponse, HttpRequest
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

from coldfront.core.allocation.models import Allocation, AllocationAttributeUsage

EOD = "T23:59:59+00:00"
HISTORY_LENGTH_MONTHS = 12


class Usage(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, *args, **kwargs):
        allocation_id_str = request.GET.get("allocation_id", "")

        start_date_str = request.GET.get("start_date", "")
        start_datetime = (
            datetime.fromisoformat(start_date_str + EOD)
            if start_date_str != ""
            else None
        )

        end_date_str = request.GET.get("end_date", date.today().isoformat())
        end_datetime = datetime.fromisoformat(end_date_str + EOD)

        allocation_id = int(allocation_id_str)

        allocation = Allocation.objects.get(pk=allocation_id)
        quota: int = allocation.get_attribute("storage_quota") * 2**10

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

        for i in range(HISTORY_LENGTH_MONTHS):
            working_datetime = _minus_months(end_datetime, i)

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

            if working_datetime == start_datetime:
                break

        return JsonResponse(
            {
                "allocation_id": allocation.pk,
                "quota": quota,
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
