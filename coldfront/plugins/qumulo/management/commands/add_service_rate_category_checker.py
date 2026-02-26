from django.core.management.base import BaseCommand
from coldfront.plugins.qumulo.management.commands.remove_subscription_option import change_subscription_to_consumption

class Command(BaseCommand):

    def handle(self, *args, **options):
        print("Changing all Subscription Service Rate Categories to Consumption")
        change_subscription_to_consumption(self)