from coldfront.plugins.qumulo.utils.storage_controller import StorageControllerFactory
from django.core.management.base import BaseCommand

import time


class Command(BaseCommand):
    def handle(self, *args, **options):
        for resource in ["Storage2", "Storage3"]:
            try:
                storage_api = StorageControllerFactory().create_connection(resource)
                print(f"Connected to ${resource} successfully")

                limit_in_bytes = 1024
                fs_path = f"/test-connection-${time.time_ns()}"

                try:
                    storage_api.create_quota(fs_path, limit_in_bytes)
                    print(
                        f"Quota created for {fs_path} with limit {limit_in_bytes} bytes"
                    )
                    storage_api.delete_quota(fs_path)
                except:
                    print("Unexpected failure creating quota")
            except:
                print(f"Failed to connect to {resource}")
