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

    def service_name(self, obj):
        return obj.service.name

    service_name.admin_order_field = "service__name"
    service_name.short_description = "Service Name"


@admin.register(ServiceRateCategoryTier)
class ServiceRateCategoryTierAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "service_rate_category",
        "rate",
        "unit_rate",
        "unit",
        "cycle",
    )

    def service_rate_category_name(self, obj):
        return obj.service_rate_category.model_name

    service_rate_category_name.admin_order_field = "service_rate_category__model_name"
    service_rate_category_name.short_description = "Service Rate Category"
