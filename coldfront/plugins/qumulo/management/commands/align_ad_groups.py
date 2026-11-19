from django.core.management.base import BaseCommand

from coldfront.plugins.qumulo.tasks_organized.align_ad_groups import align_ad_groups


class Command(BaseCommand):
    help = "Align AD groups for a specific storage group"

    def handle(self, *args, **options):
        align_ad_groups()
