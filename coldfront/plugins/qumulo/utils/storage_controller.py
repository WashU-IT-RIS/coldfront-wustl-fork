from coldfront.plugins.qumulo.utils.qumulo_api import QumuloAPI

import os, json


class StorageControllerFactory:
    def __init__(self, resource: str) -> None:
        self.resource = resource
        self.qumulo_info = json.loads(os.environ.get("QUMULO_INFO"))

    def create_connection(self):
        # placeholder for now, this will allow us to expand coverage to different resource types
        qumulo_list = ["Storage2", "Storage3"]
        if self.resource in qumulo_list:
            return self.create_qumulo_connection()
        else:
            raise ValueError(f"Unsupported resource: {self.resource}")

    def create_qumulo_connection(self):
        host = self.qumulo_info[self.resource]["host"]
        port = self.qumulo_info[self.resource]["port"]
        username = self.qumulo_info[self.resource]["user"]
        password = self.qumulo_info[self.resource]["pass"]
        # Do we need error handling here if we handle it in QumuloAPI()?
        if not all([host, port, username, password]):
            raise ValueError("Missing required Qumulo connection parameters")

        return QumuloAPI(host, port, username, password)
