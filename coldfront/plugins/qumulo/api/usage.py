import datetime

from django.http import JsonResponse, HttpRequest, HttpResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttribute,
)


class Usage(LoginRequiredMixin, View):
  def get(self, request: HttpRequest, *args, **kwargs):
    allocation_id_str = request.GET.get("allocation_id", "")
    date_str = request.GET.get("date", datetime.date.today().isoformat())
    
    if allocation_id_str == "": 
      return HttpResponse(status=200)
    
    allocation_id = int(allocation_id_str)
    
    allocation = Allocation.objects.get(pk=allocation_id)
    quota: AllocationAttribute = allocation.get_attribute("storage_quota") * 2**10
    usage = allocation.get_usage_kb_by_date(datetime.date.fromisoformat(date_str)) / 2**20
    
    return JsonResponse({"allocation_id": allocation.pk, "quota": quota, "usage": usage, "date": date_str})