from unittest.mock import MagicMock, patch
from coldfront.plugins.qumulo.services.file_system_service import FileSystemService
from coldfront.plugins.qumulo.utils.qumulo_api import QumuloAPI

PETABYTE_IN_BYTES = 1e15


from django.test import TestCase


class TestFileSystemService(TestCase):

    def setUp(self) -> None:
        self.mock_quota_response = {
            "total_size": 10.11,
            "free_size": 5.11,
            "snapshot_size": 0.005,
        }
        return super().setUp()


    @patch("coldfront.plugins.qumulo.services.QumuloAPI")
    def test_get_file_system_stats(self, qumulo_api_mock: QumuloAPI) -> None:
        qumulo_api = MagicMock()
        qumulo_api.get_file_system_stats.return_value = self.mock_quota_response
        qumulo_api_mock.return_value = qumulo_api
    
        actual_result = FileSystemService.get_file_system_stats()
        expected_result = {
            "total_size": 10.11,
            "free_size": 5.11,
            "snapshot_size": 0.005,
        }
        self.assertDictEqual(expected_result, actual_result)
