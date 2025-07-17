import os, json

from django.test import TestCase
from unittest.mock import patch, MagicMock
from coldfront.plugins.qumulo.utils.qumulo_api import QumuloAPI

from dotenv import load_dotenv

load_dotenv(override=True)


class TestQumuloAPI(TestCase):
    def test_api_connects_to_storage2_by_default(self):
        with patch(
            "coldfront.plugins.qumulo.utils.qumulo_api.RestClient"
        ) as mock_RestClient:
            qumulo_info = json.loads(os.environ.get("QUMULO_INFO"))
            host = qumulo_info["storage_2"]["host"]
            port = qumulo_info["storage_2"]["port"]
            username = qumulo_info["storage_2"]["user"]
            password = qumulo_info["storage_2"]["pass"]

            mock_login = MagicMock()
            mock_RestClient.return_value.login = mock_login

            qumulo_instance = QumuloAPI()

            mock_RestClient.assert_called_once_with(host, port)
            mock_login.assert_called_once_with(username, password)

    def test_api_takes_custom_connection(self):
        with patch(
            "coldfront.plugins.qumulo.utils.qumulo_api.RestClient"
        ) as mock_RestClient:
            custom_host = "custom_host"
            custom_port = "custom_port"
            custom_username = "custom_user"
            custom_password = "custom_pass"

            mock_login = MagicMock()
            mock_RestClient.return_value.login = mock_login

            qumulo_instance = QumuloAPI(
                host=custom_host,
                port=custom_port,
                username=custom_username,
                password=custom_password,
            )

            mock_RestClient.assert_called_once_with(custom_host, custom_port)
            mock_login.assert_called_once_with(custom_username, custom_password)

    def test_api_throws_exception_on_partial_arguments(self):
        custom_host = "custom_host"
        custom_port = "custom_port"
        custom_username = "custom_user"
        custom_password = "custom_pass"

        with self.assertRaises(ValueError):
            QumuloAPI(host=custom_host, port=custom_port, username=custom_username)

        with self.assertRaises(ValueError):
            QumuloAPI(host=custom_host, port=custom_port, password=custom_password)

        with self.assertRaises(ValueError):
            QumuloAPI(
                host=custom_host, username=custom_username, password=custom_password
            )

        with self.assertRaises(ValueError):
            QumuloAPI(
                port=custom_port, username=custom_username, password=custom_password
            )
