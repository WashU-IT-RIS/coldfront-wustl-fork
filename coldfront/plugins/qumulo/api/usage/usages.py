from datetime import date, datetime, timedelta

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

        usage_gib = []

        history = list(
            AllocationAttributeUsage.history.filter(
                allocation_attribute__allocation__pk=allocation_id,
                allocation_attribute__allocation_attribute_type__name="storage_quota",
            )
        )
        allocation_history = list(
            AllocationAttribute.history.filter(
                allocation__pk=allocation_id,
                allocation_attribute_type__name="storage_quota",
            )
        )

        if len(history) <= 0 or len(allocation_history) <= 0:
            return HttpResponseNotFound("allocation not found")

        def find_allocation_moment(usage_moment):
            for moment in allocation_history:
                if usage_moment.history_date.date() >= moment.history_date.date():
                    return moment

            return None

        mapped_history = map(
            lambda moment: {
                "datetime": moment.history_date,
                "usage": moment.value,
                "quota": int(find_allocation_moment(moment).value),
            },
            history,
        )

        working_datetime = end_datetime
        i = 0
        for moment in mapped_history:
            while (
                working_datetime >= moment["datetime"]
                and working_datetime > start_datetime
            ):
                usage_gib.insert(
                    0,
                    {
                        "date": working_datetime.date().isoformat(),
                        "usage": moment["usage"] / 2**30,
                        "quota": moment["quota"] * 2**10,
                    },
                )
                working_datetime = _minus_months(end_datetime, i)
                i = i + 1
            if working_datetime <= start_datetime:
                working_datetime = start_datetime

                if working_datetime >= moment["datetime"]:
                    usage_gib.insert(
                        0,
                        {
                            "date": working_datetime.date().isoformat(),
                            "usage": moment["usage"] / 2**30,
                            "quota": moment["quota"] * 2**10,
                        },
                    )
                    break

        return JsonResponse(
            {
                "allocation_id": allocation_id,
                "usage_data": usage_gib,
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
