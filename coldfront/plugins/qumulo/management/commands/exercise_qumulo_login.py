from django.core.management.base import BaseCommand
from coldfront.plugins.qumulo.utils.qumulo_api import QumuloAPI


class Command(BaseCommand):

    def handle(self, *args, **options):
        qumulo_api = QumuloAPI()