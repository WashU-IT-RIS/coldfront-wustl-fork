from datetime import date
from django.core.management.base import BaseCommand

from coldfront.plugins.integratedbilling.models import ServiceRateCategory


class Command(BaseCommand):

    def handle(self, *args, **options):

        ServiceRateCategory.objects.update_or_create(
            model_name="consumption",
            model_description="Consumption",
            start_date=date(2025, 10, 1),
            end_date=date(2026, 7, 1),
            tier_name="active",
            rate=6.50,
            unit_rate="1",
            unit="TB",
            cycle="monthly",
        )

        ServiceRateCategory.objects.update_or_create(
            model_name="consumption",
            model_description="Consumption",
            start_date=date(2025, 10, 1),
            end_date=date(2026, 7, 1),
            tier_name="archive",
            rate=3.15,
            unit_rate="1",
            unit="TB",
            cycle="monthly",
        )
