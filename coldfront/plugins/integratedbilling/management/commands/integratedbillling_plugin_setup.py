from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run setup script to initialize the Coldfront database"

    def handle(self, *args, **options):
        print("Running Coldfront Plugin Integrated Billing setup script")
        call_base_commands()
        print("Coldfront Plugin Integrated Billing setup script complete")


def call_base_commands():
    call_command("add_service_rate_categories_for_storage")
