from django.contrib import admin

from coldfront.core.service.models import (
    Service,
    ServiceRateCategory,
    ServiceRateCategoryTier,
)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(ServiceRateCategory)
class ServiceRateCategoryAdmin(admin.ModelAdmin):
    list_display = ("model_name",)


@admin.register(ServiceRateCategoryTier)
class ServiceRateCategoryTierAdmin(admin.ModelAdmin):
    list_display = ("name",)
