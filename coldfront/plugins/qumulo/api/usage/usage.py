from datetime import date, datetime, timedelta

from django.http import (
    JsonResponse,
    HttpRequest,
    HttpResponseBadRequest,
    HttpResponseNotFound,
)
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from coldfront.core.allocation.models import Allocation, AllocationAttributeUsage
from coldfront.core.user.models import User


EOD = "T23:59:59+00:00"


class Usage(LoginRequiredMixin, UserPassesTestMixin, View):
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
