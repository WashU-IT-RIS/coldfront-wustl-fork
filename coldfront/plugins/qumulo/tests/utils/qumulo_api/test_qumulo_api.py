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

    # Do we still need this test? I don't think it's necessary anymore since we are pretty protected from partial args

    # def test_api_throws_exception_on_partial_arguments(self):
    #     custom_host = "custom_host"
    #     custom_port = "custom_port"
    #     custom_username = "custom_user"
    #     custom_password = "custom_pass"

    #     with self.assertRaises(ValueError):
    #         StorageControllerFactory().create_connection("Storage2")

    #     with self.assertRaises(ValueError):
    #         QumuloAPI(host=custom_host, port=custom_port, password=custom_password)

    #     with self.assertRaises(ValueError):
    #         QumuloAPI(
    #             host=custom_host, username=custom_username, password=custom_password
    #         )

    #     with self.assertRaises(ValueError):
    #         QumuloAPI(
    #             port=custom_port, username=custom_username, password=custom_password
    #         )
