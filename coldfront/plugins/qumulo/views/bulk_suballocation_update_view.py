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

from coldfront.core.constants import BILLING_CYCLE_OPTIONS
from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttribute,
    AllocationAttributeType,
    AllocationAttributeChangeRequest,
    AllocationChangeRequest,
    AllocationChangeStatusChoice,
)
from coldfront.core.utils.validate import (
    AllocationAttributeValidator,
    AttributeValidator,
)
from coldfront.plugins.qumulo.constants import PROTOCOL_OPTIONS, SERVICE_RATE_CATEGORIES
from coldfront.plugins.qumulo.validators import validate_ad_users, validate_ticket


class BulkAllocationAttributeForm(forms.Form):
    attributeTypeId = forms.ModelChoiceField(
        queryset=AllocationAttributeType.objects.all()
    )
    value = forms.CharField(max_length=128, strip=False)
    allocationIds = forms.ModelMultipleChoiceField(
        queryset=Allocation.objects.filter(
            resources__resource_type__name="Storage"
        ).distinct()
    )

    def clean(self):
        cleaned_data = super().clean()
        attribute_type = cleaned_data.get("attributeTypeId")
        value = cleaned_data.get("value")
        if not attribute_type or value is None:
            return cleaned_data

        try:
            attribute_data_type = attribute_type.attribute_type.name.strip()
            attribute_validator = AttributeValidator(value)
            if attribute_data_type == "Int":
                attribute_validator.validate_int()
            elif attribute_data_type == "Float":
                attribute_validator.validate_float()
            elif attribute_data_type == "Yes/No":
                attribute_validator.validate_yes_no()
            elif attribute_data_type == "Date":
                attribute_validator.validate_date()
            elif attribute_data_type == "JSON":
                attribute_validator.validate_json()

            if attribute_type.name == "billing_cycle":
                AllocationAttributeValidator(value).validate_billing_cycle()
            elif attribute_type.name == "storage_ticket":
                value = value.upper()
                validate_ticket(value)
                if not value.startswith("ITSD-"):
                    value = f"ITSD-{value}"
                if len(value) > 128:
                    raise ValidationError(
                        "Ensure this value has at most 128 characters."
                    )
                cleaned_data["value"] = value
            elif attribute_type.name in {"billing_contact", "technical_contact"}:
                validate_ad_users([value])
            elif attribute_type.name == "service_rate_category":
                if value not in dict(SERVICE_RATE_CATEGORIES):
                    raise ValidationError("Choose a valid service rate category.")
            elif attribute_type.name == "storage_protocols":
                protocols = json.loads(value)
                valid_protocols = {option[0] for option in PROTOCOL_OPTIONS}
                if not isinstance(protocols, list) or any(
                    not isinstance(protocol, str) or protocol not in valid_protocols
                    for protocol in protocols
                ):
                    raise ValidationError("Choose valid storage protocols.")

            if attribute_type.name == "storage_quota":
                quota = int(value)
                if quota < 0 or quota > 2000:
                    raise ValidationError(
                        "Ensure this value is between 0 and 2000."
                    )
        except (ValidationError, json.JSONDecodeError) as error:
            self.add_error("value", error)

        return cleaned_data


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
            "billingCycleOptions": BILLING_CYCLE_OPTIONS,
            "protocolOptions": PROTOCOL_OPTIONS,
            "serviceRateCategories": SERVICE_RATE_CATEGORIES,
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
        new_value = form.cleaned_data["value"]
        pending_status = AllocationChangeStatusChoice.objects.get(name="Pending")
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
                    changed_attributes = []
                    for attribute in attributes:
                        if attribute.value == new_value:
                            continue

                        previous_value = attribute.value
                        attribute.value = new_value
                        attribute.full_clean()
                        attribute.value = previous_value
                        if not attribute.pk:
                            attribute.save()
                        changed_attributes.append(attribute)

                    if not changed_attributes:
                        continue

                    change_request = AllocationChangeRequest.objects.create(
                        allocation=allocation,
                        status=pending_status,
                        justification="updating",
                        notes="updating",
                        end_date_extension=10,
                        user=request.user,
                    )
                    for attribute in changed_attributes:
                        AllocationAttributeChangeRequest.objects.create(
                            allocation_attribute=attribute,
                            allocation_change_request=change_request,
                            new_value=new_value,
                        )
        except ValidationError as error:
            return JsonResponse({"error": " ".join(error.messages)}, status=400)

        return JsonResponse({"updatedAllocations": allocations.count()})