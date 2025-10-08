import os, json

from django.test import TestCase
from unittest.mock import patch, MagicMock
from coldfront.plugins.qumulo.utils.storage_controller import StorageControllerFactory

from dotenv import load_dotenv

load_dotenv(override=True)


class TestQumuloAPI(TestCase):
    def test_api_connects_to_storage2(self):
        with patch(
            "coldfront.plugins.qumulo.utils.qumulo_api.RestClient"
        ) as mock_RestClient:
            qumulo_info = json.loads(os.environ.get("QUMULO_INFO"))
            host = qumulo_info["Storage2"]["host"]
            port = qumulo_info["Storage2"]["port"]
            username = qumulo_info["Storage2"]["user"]
            password = qumulo_info["Storage2"]["pass"]

            mock_login = MagicMock()
            mock_RestClient.return_value.login = mock_login

            qumulo_instance = StorageControllerFactory().create_connection("Storage2")

            mock_RestClient.assert_called_once_with(host, port)
            mock_login.assert_called_once_with(username, password)

    def test_api_connects_to_storage3(self):
        with patch(
            "coldfront.plugins.qumulo.utils.qumulo_api.RestClient"
        ) as mock_RestClient:
            qumulo_info = json.loads(os.environ.get("QUMULO_INFO"))
            host = qumulo_info["Storage3"]["host"]
            port = qumulo_info["Storage3"]["port"]
            username = qumulo_info["Storage3"]["user"]
            password = qumulo_info["Storage3"]["pass"]

            mock_login = MagicMock()
            mock_RestClient.return_value.login = mock_login

            qumulo_instance = StorageControllerFactory().create_connection("Storage3")

            mock_RestClient.assert_called_once_with(host, port)
            mock_login.assert_called_once_with(username, password)
