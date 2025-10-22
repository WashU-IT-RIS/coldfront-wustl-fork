from datetime import date
from django.core.management.base import BaseCommand

from coldfront.core.service_rate_category.models import (
    Service,
    ServiceRateCategory,
    ServiceRateCategoryTier,
)


class Command(BaseCommand):

    def handle(self, *args, **options):

        storage_service, _ = Service.objects.update_or_create(name="Storage2")

        consumption_category, _ = ServiceRateCategory.objects.update_or_create(
            service=storage_service,
            model_name="consumption",
            model_description="Consumption",
            start_date=date(2025, 10, 1),
            end_date=date(2026, 7, 1),
        )

        ServiceRateCategoryTier.objects.update_or_create(
            name="active",
            rate=6.50,
            unit_rate="1",
            unit="TB",
            cycle="month",
            service_rate_category=consumption_category,
        )

        ServiceRateCategoryTier.objects.update_or_create(
            name="archive",
            rate=3.15,
            unit_rate="1",
            unit="TB",
            cycle="month",
            service_rate_category=consumption_category,
        )
