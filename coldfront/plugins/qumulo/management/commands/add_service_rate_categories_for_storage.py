from datetime import date
from django.core.management.base import BaseCommand

from coldfront.core.service.models import (
    Service,
    ServiceRateCategory,
    ServiceRateCategoryTier,
)


class Command(BaseCommand):

    Service.objects.update_or_create(
        name="Storage", defaults={"description": "Storage placeholder description"}
    )
    Service.objects.update_or_create(
        name="Compute2", defaults={"description": "Storage placeholder description"}
    )

    ServiceRateCategory.objects.update_or_create(
        service__name="Storage",
        model_name="consumption",
        model_description="Consumption",
        start_date=date(2025,7,1),
        end_date=date(2026,7,1),
    )

    ServiceRateCategory.objects.get_or_create(
        service__name="Storage",
        model_name="condo",
        model_description="Condo",
        start_date=date(2025,7,1),
        end_date=date(2026,7,1),
    )

    ServiceRateCategory.objects.update_or_create(
        service__name="Storage",
        model_name="subscription",
        model_description="Subscription",
        start_date=date(2025,7,1),
        end_date=date(2026,7,1),
    )

    ServiceRateCategoryTier.objects.update_or_create(
        name="active",
        rate="634",
        unit_rate="100",
        unit="TB",
        cycle="month",
        service_rate_category__model_name="subscription",
    )

    ServiceRateCategoryTier.objects.update_or_create(
        name="archive",
        rate="264",
        unit_rate="100",
        unit="TB",
        cycle="month",
        service_rate_category__model_name="subscription",
    )

    ServiceRateCategoryTier.objects.update_or_create(
        name="active",
        rate="2643",
        unit_rate="500",
        unit="TB",
        cycle="month",
        service_rate_category__model_name="subscription",
    )

    ServiceRateCategoryTier.objects.update_or_create(
        name="archive",
        rate="881",
        unit_rate="500",
        unit="TB",
        cycle="month",
        service_rate_category__model_name="subscription",
    )
