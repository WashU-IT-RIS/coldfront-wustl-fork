from django.core.management.base import BaseCommand

from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = "Create default user groups"

    def handle(self, *args, **options):
        print("Creating default user groups ...")
        groups = ["RIS-UserSupport"]
        for group in groups:
            Group.objects.get_or_create(name=group)
        print("Finished creating default user groups")
