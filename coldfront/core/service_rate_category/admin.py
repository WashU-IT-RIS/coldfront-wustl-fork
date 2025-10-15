from django.contrib import admin

from coldfront.core.service_rate_category.models import (
    Service,
    ServiceRateCategory,
    ServiceRateCategoryTier,
)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "description")


@admin.register(ServiceRateCategory)
class ServiceRateCategoryAdmin(admin.ModelAdmin):
    list_display = ("service_name", "model_name", "start_date", "end_date")


@admin.register(ServiceRateCategoryTier)
class ServiceRateCategoryTierAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "service_rate_category_model_name",
        "rate",
        "unit_rate",
        "unit",
        "cycle",
    )
