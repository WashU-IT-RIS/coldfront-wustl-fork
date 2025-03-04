from unittest.mock import MagicMock, patch
from coldfront.plugins.qumulo.services.file_system_service import FileSystemService

PETABYTE_IN_BYTES = 1e15


from django.test import TestCase


class TestFileSystemService(TestCase):

    def setUp(self) -> None:
        self.mock_quota_response = {
            "block_size_bytes": 4096,
            "total_size_bytes": "5498921790996480",
            "free_size_bytes": "1449206347350016",
            "snapshot_size_bytes": "181465474080768",
        }
        self.expected_result = {
            "total_size": 5.4989,
            "free_size": 1.4492,
            "snapshot_size": 0.1815,
        }
        return super().setUp()

    @patch("coldfront.plugins.qumulo.services.file_system_service.QumuloAPI")
    def test_get_file_system_stats(self, qumulo_api_mock: MagicMock) -> None:
        qumulo_api = MagicMock()
        qumulo_api.get_file_system_stats.return_value = self.mock_quota_response
        qumulo_api_mock.return_value = qumulo_api

        actual_result = FileSystemService.get_file_system_stats()
        self.assertDictEqual(self.expected_result, actual_result)
