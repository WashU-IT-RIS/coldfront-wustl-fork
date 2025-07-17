from django.test import TestCase, tag
from coldfront.plugins.qumulo.utils.qumulo_api import QumuloAPI
import os
import json


class TestQumuloApiInit(TestCase):
    @tag("integration")
    def test_logs_in_without_throwing_error(self):
        try:
            qumulo_api = QumuloAPI()
        except:
            self.fail("Login failed!")

    # These variables should be in .env file
    @tag("integration")
    def test_logs_into_specific_server(self):
        qumulo_info = json.loads(os.environ.get("QUMULO_INFO"))
        host = qumulo_info["storage_3"]["host"]
        port = qumulo_info["storage_3"]["port"]
        username = qumulo_info["storage_3"]["user"]
        password = qumulo_info["storage_3"]["pass"]

        try:
            qumulo_api = QumuloAPI(
                host=host, port=port, username=username, password=password
            )
        except:
            self.fail("Login failed!")

    # Used qumulo poc to set custom api values
    @tag("integration")
    def test_can_have_2_connections(self):
        qumulo_info = json.loads(os.environ.get("QUMULO_INFO"))
        host = qumulo_info["storage_3"]["host"]
        port = qumulo_info["storage_3"]["port"]
        username = qumulo_info["storage_3"]["user"]
        password = qumulo_info["storage_3"]["pass"]

        try:
            default_qumulo_api = QumuloAPI()
        except:
            self.fail("Login failed!")

        try:
            custom_qumulo_api = QumuloAPI(
                host=host, port=port, username=username, password=password
            )
        except:
            self.fail("Login failed!")

        self.assertNotEqual(
            default_qumulo_api.list_nfs_exports(), custom_qumulo_api.list_nfs_exports()
        )
