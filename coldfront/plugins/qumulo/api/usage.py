from datetime import date, datetime

from django.utils import timezone
# from django.utils.dateparse import parse_date
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

from coldfront.core.allocation.models import Allocation, AllocationAttributeUsage


class Usage(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, *args, **kwargs):
        allocation_id_str = request.GET.get("allocation_id", "")
        start_date_str = request.GET.get("start_date", "")
        start_date = date.fromisoformat(f"{start_date_str}") if start_date_str != "" else None
        end_date_str = request.GET.get("end_date", date.today().isoformat())
        end_date = date.fromisoformat(end_date_str)

        if allocation_id_str == "":
            return HttpResponse(status=200)

        allocation_id = int(allocation_id_str)

        allocation = Allocation.objects.get(pk=allocation_id)
        quota: int = allocation.get_attribute("storage_quota") * 2**10

        usage_gib = []
        latest_usage = AllocationAttributeUsage.objects.get(
            allocation_attribute__allocation=allocation,
            allocation_attribute__allocation_attribute_type__name="storage_quota",
        ).history.most_recent()
        usage_gib.append(
            {"date": end_date_str, "usage": latest_usage.value / 2**30}
        )

        for i in range(12):
            current_month = end_date.month
            new_month = current_month - i

            if new_month > 0:
                working_date = end_date.replace(day=1, month=new_month)
            else:
                new_month = current_month - i + 12
                working_date = end_date.replace(day=1, month=new_month, year=end_date.year - 1)
                
            if isinstance(start_date, date) and start_date > working_date:
              break        

            current_timezone = timezone.get_default_timezone()
            datetime_str = working_date.isoformat() + "T00:00:00"
            foo = datetime.fromisoformat(datetime_str)
            working_usage: AllocationAttributeUsage = (
                AllocationAttributeUsage.history.as_of(current_timezone.fromutc(foo))
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
                        "date": working_date.isoformat(),
                        "usage": working_usage.value / 2**30,
                    },
                )

        return JsonResponse(
            {
                "allocation_id": allocation.pk,
                "quota": quota,
                "usage": usage_gib,
            }
        )
