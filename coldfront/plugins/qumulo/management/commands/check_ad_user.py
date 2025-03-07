from coldfront.plugins.qumulo.utils.active_directory_api import ActiveDirectoryAPI
from django.core.management.base import BaseCommand

class Command(BaseCommand):

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "wustl_key", type=str, help="A user's WUSTL Key"
        )


    def handle(self, *args, **options) -> None:
        wustl_key = options["wustl_key"]
        active_directory_api = ActiveDirectoryAPI()
        try:
            result = active_directory_api.get_user(wustl_key)
            print(f"{wustl_key} is a valid WUSTL Key")
            print(f"Result: {result}")
        except ValueError:
            print(f"{wustl_key} is not a valid WUSTL Key")
