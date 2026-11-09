from django.core.management.base import BaseCommand


from coldfront.plugins.qumulo.tasks_organized.align_AD_groups import align_ad_groups

import time


class Command(BaseCommand):
    help = "Align AD groups for a specific storage group"

    def handle(self, *args, **options):
        print("Running Align AD Groups")

        start = time.time()
        for x in range(5):
            align_ad_groups("storage2-harterj-test-020606-01-rw")
        end = time.time()
        print(f"Align AD Groups completed in {end - start} seconds")
