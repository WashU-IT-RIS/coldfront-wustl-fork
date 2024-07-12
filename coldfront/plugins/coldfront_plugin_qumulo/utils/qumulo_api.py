import logging
import os
import time
import urllib.parse
from qumulo.lib.request import RequestError
from qumulo.rest_client import RestClient
from qumulo.commands.nfs import parse_nfs_export_restrictions
from dotenv import load_dotenv
from typing import Optional

load_dotenv(override=True)


class QumuloAPI:
    def __init__(self):
        self.rc: RestClient = RestClient(
            os.environ.get("QUMULO_HOST"), os.environ.get("QUMULO_PORT")
        )
        self.rc.login(os.environ.get("QUMULO_USER"), os.environ.get("QUMULO_PASS"))
        self.valid_protocols = ["s3", "nfs", "smb"]

    def create_allocation(
        self,
        protocols: list[str],
        export_path: str,
        fs_path: str,
        name: str,
        limit_in_bytes: int,
    ):
        if name == None:
            raise ValueError("name must be defined.")

        if fs_path == None or not fs_path.startswith("/"):
            raise ValueError("fs_path should be defined and absolute.")

        if not protocols:
            raise ValueError("protocols must be defined.")

        self.validate_protocols(protocols)

        for protocol in protocols:
            self.create_protocol(
                export_path=export_path, fs_path=fs_path, name=name, protocol=protocol
            )

        self.create_quota(fs_path=fs_path, limit_in_bytes=limit_in_bytes)

    def create_protocol(self, export_path: str, fs_path: str, name: str, protocol: str):
        if name == None:
            raise ValueError("name must be defined.")

        if fs_path == None or not fs_path.startswith("/"):
            raise ValueError("fs_path should be defined and absolute.")

        self.validate_protocol(protocol=protocol)

        if protocol == "s3":
            self.rc.s3.create_bucket(name=name, path=fs_path, create_path=True)
        if protocol == "nfs":
            if export_path == None or not export_path.startswith("/"):
                raise ValueError("export_path should be defined and absolute.")

            nfs_restrictions = [
                {
                    "host_restrictions": [],
                    "user_mapping": "NFS_MAP_NONE",
                    "require_privileged_port": False,
                    "read_only": False,
                }
            ]

            self.rc.nfs.nfs_add_export(
                export_path=export_path,
                fs_path=fs_path,
                description=name,
                restrictions=parse_nfs_export_restrictions(nfs_restrictions),
                allow_fs_path_create=True,
                tenant_id=1,
            )
        if protocol == "smb":
            self.rc.smb.smb_add_share(
                share_name=name,
                fs_path=fs_path,
                description=name,
                allow_fs_path_create=True,
            )

    def create_quota(self, fs_path: str, limit_in_bytes: int):
        file_attr = self.rc.fs.get_file_attr(path=fs_path)

        return self.rc.quota.create_quota(file_attr["id"], limit_in_bytes)

    def _delete_allocation(
        self,
        protocols: list[str],
        fs_path: str,
        export_path: Optional[str] = None,
        name: Optional[str] = None,
    ):
        self.validate_protocols(protocols=protocols)

        self.delete_quota(fs_path)

        for protocol in protocols:
            self.delete_protocol(export_path=export_path, name=name, protocol=protocol)

    def delete_protocol(
        self,
        protocol: str,
        export_path: Optional[str] = None,
        name: Optional[str] = None,
    ):
        self.validate_protocol(protocol=protocol)
        if protocol == "nfs":
            if not export_path:
                raise TypeError("Export path is not defined.")
            storage_id = self.get_id(protocol=protocol, export_path=export_path)
            self.rc.nfs.nfs_delete_export(storage_id)
        if protocol == "s3":
            if not name:
                raise TypeError("Name is not defined.")
            self.rc.s3.delete_bucket(name=name, delete_root_dir=False)
        if protocol == "smb":
            if not name:
                raise TypeError("Name is not defined.")
            storage_id = self.get_id(protocol=protocol, name=name)
            self.rc.smb.smb_delete_share(storage_id)

    def delete_nfs_export(self, export_id):
        return self.rc.nfs.nfs_delete_export(export_id)

    def delete_quota(self, fs_path: str):
        file_attr = self.rc.fs.get_file_attr(path=fs_path)

        return self.rc.quota.delete_quota(file_attr["id"])

    def delete_nfs_export(self, export_id):
        return self.rc.nfs.nfs_delete_export(export_id)

    def get_file_attributes(self, path):
        return self.rc.fs.get_file_attr(path=path)

    def get_id(
        self,
        protocol: str,
        export_path: Optional[str] = None,
        name: Optional[str] = None,
    ):
        if protocol not in ["nfs", "smb"]:
            raise ValueError("Invalid Protocol")

        if protocol == "nfs":
            export = self.rc.request(
                method="GET",
                uri="/v2/nfs/exports/" + urllib.parse.quote(export_path, safe=""),
            )
        elif protocol == "smb":
            export = self.rc.request(
                method="GET", uri="/v2/smb/shares/" + urllib.parse.quote(name, safe="")
            )

        return export["id"]

    def list_nfs_exports(self):
        return self.rc.nfs.nfs_list_exports()

    def update_allocation(
        self,
        protocols: list[str],
        export_path: str = None,
        fs_path: str = None,
        name: str = None,
        limit_in_bytes: int = 0,
    ):
        if not protocols:
            raise ValueError("protocols should be defined.")

        self.validate_protocols(protocols=protocols)

        for protocol in self.valid_protocols:
            if protocol in protocols:
                try:
                    self.create_protocol(
                        export_path=export_path,
                        fs_path=fs_path,
                        name=name,
                        protocol=protocol,
                    )
                except RequestError as e:
                    logging.info(f"{protocol} protocol already exists.")
            else:
                try:
                    self.delete_protocol(
                        export_path=export_path, name=name, protocol=protocol
                    )
                except RequestError as e:
                    logging.info(f"{protocol} protocol does not exist.")
                except TypeError as e:
                    if str(e) not in [
                        "Name is not defined.",
                        "Export path is not defined.",
                    ]:
                        raise
                    else:
                        logging.warn("Name or Export Path is not defined.")

        self.update_quota(fs_path=fs_path, limit_in_bytes=limit_in_bytes)

    def update_nfs_export(
        self, export_id, export_path=None, fs_path=None, description=None
    ):
        return self.rc.nfs.nfs_modify_export(
            export_id=export_id,
            export_path=export_path,
            fs_path=fs_path,
            description=description,
            allow_fs_path_create=True,
        )

    def update_quota(self, fs_path: str, limit_in_bytes: int):
        file_attr = self.rc.fs.get_file_attr(path=fs_path)
        return self.rc.quota.update_quota(file_attr["id"], limit_in_bytes)

    def validate_protocol(self, protocol: str):
        if protocol not in self.valid_protocols:
            raise ValueError(protocol, " protocol is not valid.")

    def validate_protocols(self, protocols: list[str]):
        for protocol in protocols:
            self.validate_protocol(protocol)

    def get_all_quotas_with_usage(self, page_size = None, if_match = None) -> str :
        tries = 0
        MAX_TRIES = 3 # move to configurable constant
        SNOOZE = 15
        all_quotas_with_usage = None

        while (tries < MAX_TRIES):
            try:
                tries = tries + 1
                # TODO: check for malformed JSON and check response code if available
                all_quotas_with_usage = self.rc.quota.get_all_quotas_with_status(page_size, if_match)
                break
            except Exception as e:
                logging.warn(f"Unable to access the QUMULO API; attempt #{tries}.")
                # Don't bother sleeping after the last failed attempt
                if tries < MAX_TRIES: time.sleep(SNOOZE)
        
        if all_quotas_with_usage is None:
            raise Exception("Unable to get_all_quotas_with_status from QUMULO API")
        
        return next(iter(all_quotas_with_usage))