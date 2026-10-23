import json

from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpRequest, JsonResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import TemplateView

from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttribute,
    AllocationAttributeType,
)


class BulkAllocationAttributeForm(forms.Form):
    attributeTypeId = forms.ModelChoiceField(
        queryset=AllocationAttributeType.objects.all()
    )
    value = forms.CharField(max_length=8192, strip=False)
    allocationIds = forms.ModelMultipleChoiceField(
        queryset=Allocation.objects.filter(
            resources__resource_type__name="Storage"
        ).distinct()
    )


@method_decorator(ensure_csrf_cookie, name="dispatch")
class BulkSubAllocationUpdateView(
    LoginRequiredMixin, UserPassesTestMixin, TemplateView
):
    template_name = "bulk_suballocation_update.html"

    def test_func(self):
        return self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        allocation_attributes = ["cost_center", "department_number", "technical_contact", "billing_contact", "billing_cycle", "service_rate_category", "storage_quota", "storage_protocols", "storage_ticket"]
        context["bulk_attribute_config"] = {
            "attributeTypes": list(
                AllocationAttributeType.objects.filter(name__in=allocation_attributes).order_by("name", "pk").values(
                    "id", "name", "attribute_type__name"
                )
            ),
            "updateUrl": reverse("qumulo:bulk-suballocation-update"),
        }
        return context

    def post(self, request: HttpRequest, *args, **kwargs):
        try:
            body = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({"error": "Invalid JSON body."}, status=400)

        if not isinstance(body, dict) or not isinstance(body.get("value"), str):
            return JsonResponse(
                {"error": "Provide an attribute, a text value and allocation IDs."},
                status=400,
            )

        form = BulkAllocationAttributeForm(body)
        if not form.is_valid():
            errors = [
                f"{field}: {message}"
                for field, messages in form.errors.items()
                for message in messages
            ]
            return JsonResponse({"error": " ".join(errors)}, status=400)

        attribute_type = form.cleaned_data["attributeTypeId"]
        allocations = Allocation.objects.filter(
            pk__in=form.cleaned_data["allocationIds"].values("pk")
        )
        try:
            with transaction.atomic():
                for allocation in allocations.select_for_update().order_by("pk"):
                    attributes = list(
                        AllocationAttribute.objects.filter(
                            allocation=allocation,
                            allocation_attribute_type=attribute_type,
                        )
                    )
                    if not attributes:
                        attributes = [
                            AllocationAttribute(
                                allocation=allocation,
                                allocation_attribute_type=attribute_type,
                            )
                        ]
                    for attribute in attributes:
                        attribute.value = form.cleaned_data["value"]
                        attribute.full_clean()
                        attribute.save()
        except ValidationError as error:
            return JsonResponse({"error": " ".join(error.messages)}, status=400)

        return JsonResponse({"updatedAllocations": allocations.count()})