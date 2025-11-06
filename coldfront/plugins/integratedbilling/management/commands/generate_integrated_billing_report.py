import argparse
from datetime import datetime
from icecream import ic

from django.core.management.base import BaseCommand, CommandError

from coldfront.plugins.integratedbilling.constants import ServiceRateTiers
from coldfront.plugins.integratedbilling.report_generator import (
    ReportGenerator,
)


class Command(BaseCommand):

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--usage-date",
            type=str,
            help="The usage_date in YYYY-MM-DD format(Ex: 2025-11-01), defaults to today if not provided",
        )

        parser.add_argument(
            "--ingest-data",
            action=argparse.BooleanOptionalAction,
            help="Ingest_data from ITSM and Coldfront: (True or False) Defaults to True",
        )

        parser.add_argument(
            "--tier",
            type=str,
            default=ServiceRateTiers.active.name,
            help="The tier to filter by (Ex: active, archive), defaults to 'active' if not provided",
        )

        parser.add_argument(
            "--delivery-date",
            type=str,
            help="The delivery date in YYYY-MM-DD format (Ex: 2025-10-01), defaults to this day of next month if not provided",
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Generates report but does not deliver it",
        )

    def handle(self, *args, **options) -> None:
        usage_date = options["usage_date"]
        ic(usage_date)
        usage_date_timestamp = (
            self.get_date_from_option("usage_date", usage_date)
            if usage_date is not None
            else None
        )
        ic(usage_date_timestamp)

        ingest_data = options["ingest_data"]
        if ingest_data is None:
            ingest_data = True
        ic(ingest_data)

        tier = self.get_valid_tier(options["tier"])
        ic(tier)

        delivery_date = options["delivery_date"]
        ic(delivery_date)
        delivery_date_timestamp = (
            self.get_date_from_option("delivery_date", delivery_date)
            if delivery_date is not None
            else None
        )
        ic(delivery_date_timestamp)

        dry_run = options["dry_run"]
        ic(dry_run)

        report_generator = ReportGenerator(
            usage_date=usage_date_timestamp,
            delivery_date=delivery_date_timestamp,
            tier=tier,
        )
        result = report_generator.generate(ingest_usages=ingest_data, dry_run=dry_run)
        ic(result)
        ic("Integrated Billing Report generation complete")

    def get_date_from_option(self, date_option: str, date_str: str) -> datetime:
        if date_option not in ["usage_date", "delivery_date"]:
            raise ValueError(f"Invalid date option: {date_option}")

        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise CommandError(
                f'Invalid date format for {date_option}: "{date_str}". Please use YYYY-MM-DD.'
            )

    def get_valid_tier(self, tier: str) -> str:
        tier = tier.lower()
        if tier not in ServiceRateTiers._member_names_:
            raise CommandError(
                f'Invalid tier: "{tier}". Valid options are: {", ".join(ServiceRateTiers._value2member_map_.keys())}.'
            )
        return tier
