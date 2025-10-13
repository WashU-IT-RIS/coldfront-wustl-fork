from coldfront.plugins.qumulo.utils.storage_controller import StorageControllerFactory
from qumulo.commands.nfs import parse_nfs_export_restrictions
from django.core.management.base import BaseCommand

import time


class Command(BaseCommand):
    def handle(self, *args, **options):
        for storage_name in ["Storage2", "Storage3"]:
            self.test_connection(storage_name)

    def test_connection(storage_name: str) -> None:
        try:
            storage_api = StorageControllerFactory().create_connection(storage_name)
            print(f"Connected to {storage_name} successfully")

            limit_in_bytes = 1024
            fs_path = f"/test-connection-{time.time_ns()}"
            export_path = fs_path
            nfs_restrictions = [
                {
                    "host_restrictions": [],
                    "user_mapping": "NFS_MAP_NONE",
                    "require_privileged_port": False,
                    "read_only": False,
                }
            ]

            storage_api.rc.nfs.nfs_add_export(
                export_path=export_path,
                fs_path=fs_path,
                description=export_path,
                restrictions=parse_nfs_export_restrictions(nfs_restrictions),
                allow_fs_path_create=True,
                tenant_id=1,
            )

            try:
                storage_api.create_quota(fs_path, limit_in_bytes)
                print(f"Quota created for {fs_path} with limit {limit_in_bytes} bytes")
                # storage_api.delete_quota(fs_path)
            except Exception as e:
                print(f"Failed to create quota for {fs_path}: {e}")

            # export_id = storage_api.get_id(protocol="nfs", export_path=export_path)
            # storage_api.delete_nfs_export(export_id)
            # storage_api.rc.fs.delete(fs_path)
        except:
            print(f"Failed to connect to {storage_name}")
