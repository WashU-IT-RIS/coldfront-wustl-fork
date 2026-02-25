from coldfront.plugins.qumulo.utils.qumulo_api import QumuloAPI

import os, json
from typing import Dict


class StorageControllerFactory:
    def __init__(self) -> None:
        self.qumulo_info = json.loads(os.environ.get("QUMULO_INFO"))

    def create_connection(self, resource: str) -> QumuloAPI:
        # placeholder for now, this will allow us to expand coverage to different resource types
        qumulo_list = ["Storage2", "Storage3"]
        if resource in qumulo_list:
            connection_info = {
                "host": self.qumulo_info[resource]["host"],
                "port": self.qumulo_info[resource]["port"],
                "user": self.qumulo_info[resource]["user"],
                "pass": self.qumulo_info[resource]["pass"],
            }
            return self.create_qumulo_connection(connection_info)
        else:
            raise ValueError(f"Unsupported resource: {resource}")

    def create_qumulo_connection(self, connection_info: Dict[str, str]) -> QumuloAPI:
        if len(connection_info) != 4:
            raise ValueError(
                "Connection info must contain host, port, user, and password."
            )
        return QumuloAPI(connection_info)
