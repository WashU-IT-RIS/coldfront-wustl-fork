from django.contrib import admin

from coldfront.plugins.integratedbilling.models import ServiceRateCategory


@admin.register(ServiceRateCategory)
class ServiceRateCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "tier_name",
        "model_name",
        "model_display_name",
        "model_description",
        "start_date",
        "end_date",
        "rate",
        "unit_rate",
        "unit",
        "cycle",
    )
    search_fields = ("tier_name", "model_name", "cycle", "start_date", "end_date")
    ordering = ("-start_date", "-end_date", "model_name", "tier_name")
