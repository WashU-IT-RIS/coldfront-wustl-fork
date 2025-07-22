from coldfront.plugins.qumulo.utils.qumulo_api import QumuloAPI

import os, json


class StorageControllerFactory:
    def __init__(self, resource):
        self.resource = resource
        self.qumulo_info = json.loads(os.environ.get("QUMULO_INFO"))

    def create_connection(self):
        # placeholder for now, this will allow us to expand coverage to different resource types
        qumulo_list = ["Storage2", "Storage3"]
        if self.resource in qumulo_list:
            return self.create_qumulo_connection()
        else:
            raise ValueError(f"Unsupported resource: {self.resource}")

    @staticmethod
    def create_qumulo_connection(self):
        host = self.qumulo_info[self.resource]["host"]
        port = self.qumulo_info[self.resource]["port"]
        username = self.qumulo_info[self.resource]["user"]
        password = self.qumulo_info[self.resource]["pass"]
        return QumuloAPI(host, port, username, password)
