from datetime import date
from icecream import ic

from django.core.management.base import BaseCommand

from coldfront.plugins.integratedbilling.report_generator import (
    ReportGenerator,
)

class Command(BaseCommand):

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "usage_date", type=date, help="The usage_date (Ex: 2025-01-01)"
        )

        parser.add_argument(
            "ingest_data", type=bool, help="The ingest_data from ITSM and Coldfront"
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Generates report but does not deliver it",
        )

    def handle(self, *args, **options) -> None:
        usage_date = options["usage_date"]  or date.today()
        ic(usage_date)

        ingest_data = options["ingest_data"] or True
        ic(ingest_data)

        dry_run = options["dry_run"] or False
        ic(dry_run)

        report_generator = ReportGenerator(usage_date)
        result = report_generator.generate(ingest_usages=ingest_data, dry_run=dry_run)
        ic(result)
