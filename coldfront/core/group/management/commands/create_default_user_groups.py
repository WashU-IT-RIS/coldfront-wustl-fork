from django.core.management.base import BaseCommand

from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission

DEFAULT_RIS_USER_GROUPS = [{"name": "RIS-UserSupport", "permissions": []}]


class Command(BaseCommand):
    """
    Command to create default user groups.
    """

    help = "Create default user groups"

    def handle(self, *args, **options):
        print("Creating default user groups ...")
        for group in DEFAULT_RIS_USER_GROUPS:
            Group.objects.get_or_create(name=group["name"])
        print("Finished creating default user groups")
