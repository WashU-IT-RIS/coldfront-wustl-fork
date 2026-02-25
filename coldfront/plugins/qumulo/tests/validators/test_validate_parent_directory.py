import os
import json

from django.test import TestCase
from unittest.mock import patch, MagicMock

from django.core.exceptions import ValidationError

from coldfront.plugins.qumulo.validators import validate_parent_directory
from coldfront.plugins.qumulo.tests.test_forms import mock_qumulo_info

mock_response = {
    "control": ["PRESENT"],
    "posix_special_permissions": ["STICKY_BIT"],
    "aces": [
        {
            "type": "ALLOWED",
            "flags": ["OBJECT_INHERIT"],
            "trustee": {
                "domain": "LOCAL",
                "auth_id": "string",
                "uid": 0,
                "gid": 0,
                "sid": "string",
                "name": "string",
            },
            "rights": ["READ"],
        }
    ],
}


class TestValidateParentDirectory(TestCase):
    def setUp(self):
        patch.dict(
            os.environ,
            {"QUMULO_INFO": json.dumps(mock_qumulo_info)},
        ).start()

        self.mock_factory = patch(
            "coldfront.plugins.qumulo.validators.StorageControllerFactory"
        ).start()

        self.mock_qumulo_api = MagicMock()
        self.mock_factory.return_value.create_connection.return_value = (
            self.mock_qumulo_api
        )

        self.mock_get_file_attr = MagicMock()
        self.mock_get_file_attr.return_value = mock_response
        self.mock_qumulo_api.rc.fs.get_file_attr = self.mock_get_file_attr

        return super().setUp()

    def tearDown(self):
        patch.stopall()

        return super().tearDown()

    def test_returns_valid_for_root(self):
        try:
            validate_parent_directory("/test-dir", "Storage2")
        except Exception:
            self.fail()

    def test_returns_invalid_for_child_with_bad_parent(self):
        self.mock_get_file_attr.side_effect = Exception()

        with self.assertRaises(ValidationError):
            validate_parent_directory("/test/test-dir/other", "Storage2")

    def test_returns_valid_for_child_with_good_parent(self):
        try:
            validate_parent_directory("/test/test-dir/more", "Storage2")
        except Exception:
            self.fail()
