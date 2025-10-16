from django.test import TestCase, tag
from coldfront.plugins.qumulo.utils.qumulo_api import QumuloAPI
from coldfront.plugins.qumulo.utils.storage_controller import StorageControllerFactory
import os
import json


class TestQumuloApiInit(TestCase):
    @tag("integration")
    def test_logs_in_without_throwing_error(self):
        try:
            qumulo_api = StorageControllerFactory().create_connection("Storage2")
        except:
            self.fail("Login failed!")

    # These variables should be in .env file
    @tag("integration")
    def test_logs_into_specific_server(self):
        qumulo_info = json.loads(os.environ.get("QUMULO_INFO"))
        host = qumulo_info["Storage3"]["host"]
        port = qumulo_info["Storage3"]["port"]
        username = qumulo_info["Storage3"]["user"]
        password = qumulo_info["Storage3"]["pass"]

        try:
            qumulo_api = StorageControllerFactory().create_connection("Storage3")
        except:
            self.fail("Login failed!")

    # Used qumulo poc to set custom api values
    @tag("integration")
    def test_can_have_2_connections(self):
        qumulo_info = json.loads(os.environ.get("QUMULO_INFO"))
        host = qumulo_info["Storage3"]["host"]
        port = qumulo_info["Storage3"]["port"]
        username = qumulo_info["Storage3"]["user"]
        password = qumulo_info["Storage3"]["pass"]

        try:
            default_qumulo_api = StorageControllerFactory().create_connection(
                "Storage2"
            )
        except:
            self.fail("Login failed!")

        try:
            custom_qumulo_api = StorageControllerFactory().create_connection("Storage3")
        except:
            self.fail("Login failed!")

        self.assertNotEqual(
            default_qumulo_api.list_nfs_exports(), custom_qumulo_api.list_nfs_exports()
        )
