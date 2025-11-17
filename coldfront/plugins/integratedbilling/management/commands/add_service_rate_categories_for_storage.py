from datetime import date
from django.core.management.base import BaseCommand

from coldfront.plugins.integratedbilling.constants import ServiceTiers
from coldfront.plugins.integratedbilling.models import ServiceRateCategory


class Command(BaseCommand):

    def handle(self, *args, **options):

        ServiceRateCategory.objects.update_or_create(
            start_date=date(2025, 10, 1),
            end_date=date(2026, 7, 1),
            rate=6.50,
            unit_rate="1",
            defaults={
                "model_name": "consumption",
                "cycle": "monthly",
                "unit": "TB",
                "tier_name": ServiceTiers.Active.name,
            },
        )

        ServiceRateCategory.objects.update_or_create(
            start_date=date(2025, 10, 1),
            end_date=date(2026, 7, 1),
            rate=3.15,
            unit_rate="1",
            defaults={
                "model_name": "consumption",
                "cycle": "monthly",
                "unit": "TB",
                "tier_name": ServiceTiers.Archive.name,
            },
        )
