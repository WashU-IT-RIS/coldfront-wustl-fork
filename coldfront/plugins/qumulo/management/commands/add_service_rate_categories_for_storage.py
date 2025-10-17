from datetime import date
from django.core.management.base import BaseCommand

from coldfront.core.service_rate_category.models import (
    Service,
    ServiceRateCategory,
    ServiceRateCategoryTier,
)


class Command(BaseCommand):

    def handle(self, *args, **options):
        storage_2_service, _ = Service.objects.update_or_create(
            name="Storage2",
            defaults={"description": "Storage 2 placeholder description"},
        )

        storage_1_service, _ = Service.objects.update_or_create(
            name="Storage1",
            defaults={"description": "Storage 1 placeholder description"},
        )

        Service.objects.update_or_create(
            name="Compute2",
            defaults={"description": "Compute 2 placeholder description"},
        )

        consumption_category, _ = ServiceRateCategory.objects.update_or_create(
            service=storage_2_service,
            model_name="consumption",
            model_description="Consumption",
            start_date=date(2025, 7, 1),
            end_date=date(2026, 7, 1),
        )

        condo_category, _ = ServiceRateCategory.objects.get_or_create(
            service=storage_2_service,
            model_name="condo",
            model_description="Condo",
            start_date=date(2025, 7, 1),
            end_date=date(2026, 7, 1),
        )

        subscription_category, _ = ServiceRateCategory.objects.update_or_create(
            service=storage_2_service,
            model_name="subscription",
            model_description="Subscription",
            start_date=date(2025, 7, 1),
            end_date=date(2026, 7, 1),
        )

        ServiceRateCategoryTier.objects.update_or_create(
            name="active",
            rate="634",
            unit_rate="100",
            unit="TB",
            cycle="month",
            service_rate_category=subscription_category,
        )

        ServiceRateCategoryTier.objects.update_or_create(
            name="archive",
            rate="264",
            unit_rate="100",
            unit="TB",
            cycle="month",
            service_rate_category=subscription_category,
        )

        ServiceRateCategoryTier.objects.update_or_create(
            name="active",
            rate="2643",
            unit_rate="500",
            unit="TB",
            cycle="month",
            service_rate_category=subscription_category,
        )

        ServiceRateCategoryTier.objects.update_or_create(
            name="archive",
            rate="881",
            unit_rate="500",
            unit="TB",
            cycle="month",
            service_rate_category=subscription_category,
        )


        ServiceRateCategoryTier.objects.update_or_create(
            name="active",
            rate="13",
            unit_rate="1",
            unit="TB",
            cycle="month",
            service_rate_category=consumption_category,
        )

        ServiceRateCategoryTier.objects.update_or_create(
            name="archive",
            rate="5",
            unit_rate="1",
            unit="TB",
            cycle="month",
            service_rate_category=consumption_category,
        )

        ServiceRateCategoryTier.objects.update_or_create(
            name="active",
            rate="529",
            unit_rate="500",
            unit="TB",
            cycle="month",
            service_rate_category=condo_category,
        )

        ServiceRateCategoryTier.objects.update_or_create(
            name="archive",
            rate="211",
            unit_rate="500",
            unit="TB",
            cycle="month",
            service_rate_category=condo_category,
        )
