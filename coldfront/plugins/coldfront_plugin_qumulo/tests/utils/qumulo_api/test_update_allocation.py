from django.test import TestCase
from unittest.mock import call, patch, MagicMock
from coldfront_plugin_qumulo.utils.qumulo_api import QumuloAPI
from qumulo.lib.request import RequestError


@patch("coldfront_plugin_qumulo.utils.qumulo_api.RestClient")
class UpdateAllocation(TestCase):
    def test_rejects_when_missing_protocol(self, mock_RestClient: MagicMock):
        qumulo_instance = QumuloAPI()

        with self.assertRaises(ValueError):
            qumulo_instance.update_allocation(
                protocols=None,
                export_path="/foo",
                fs_path="/bar",
                name="bar",
                limit_in_bytes=10**9,
            )

    def test_rejects_when_protocols_is_empty(self, mock_RestClient: MagicMock):
        qumulo_instance = QumuloAPI()

        with self.assertRaises(ValueError):
            qumulo_instance.update_allocation(
                protocols=[],
                export_path="/foo",
                fs_path="/bar",
                name="bar",
                limit_in_bytes=10**9,
            )

    def test_rejects_when_incorrect_protocol(self, mock_RestClient: MagicMock):
        qumulo_instance = QumuloAPI()

        with self.assertRaises(ValueError):
            qumulo_instance.update_allocation(
                protocols=["bad_protocol"],
                export_path="/foo",
                fs_path="/bar",
                name="bar",
                limit_in_bytes=10**9,
            )

    def test_rejects_if_some_protocols_are_bad(self, mock_RestClient: MagicMock):
        qumulo_instance = QumuloAPI()

        with self.assertRaises(ValueError):
            qumulo_instance.update_allocation(
                protocols=["nfs", "bad_protocol", "s3"],
                export_path="/foo",
                fs_path="/bar",
                name="bar",
                limit_in_bytes=10**9,
            )

    def test_adds_nfs_export(self, mock_RestClient: MagicMock):
        qumulo_instance = QumuloAPI()

        with patch.object(
            QumuloAPI, "create_protocol", MagicMock()
        ) as mock_create_protocol:
            qumulo_instance.update_allocation(
                protocols=["nfs"],
                export_path="/foo",
                fs_path="/bar",
                name="bar",
                limit_in_bytes=10**9,
            )

            mock_create_protocol.assert_called_once_with(
                protocol="nfs", export_path="/foo", fs_path="/bar", name="bar"
            )

    def test_adds_s3_bucket(self, mock_RestClient: MagicMock):
        qumulo_instance = QumuloAPI()

        with patch.object(
            QumuloAPI, "create_protocol", MagicMock()
        ) as mock_create_protocol:
            qumulo_instance.update_allocation(
                protocols=["s3"],
                export_path=None,
                fs_path="/bar",
                name="bar",
                limit_in_bytes=10**9,
            )

            mock_create_protocol.assert_called_once_with(
                protocol="s3", export_path=None, fs_path="/bar", name="bar"
            )

    def test_adds_smb_share(self, mock_RestClient: MagicMock):
        qumulo_instance = QumuloAPI()
        with patch.object(
            QumuloAPI, "create_protocol", MagicMock()
        ) as mock_create_protocol:
            qumulo_instance.update_allocation(
                protocols=["smb"],
                export_path="/foo",
                fs_path="/bar",
                name="bar",
                limit_in_bytes=10**9,
            )

            mock_create_protocol.assert_called_once_with(
                protocol="smb", export_path="/foo", fs_path="/bar", name="bar"
            )

    def test_adds_nfs_smb_and_deletes_s3(self, mock_RestClient: MagicMock):
        qumulo_instance = QumuloAPI()

        with patch.object(
            QumuloAPI, "create_protocol", MagicMock()
        ) as mock_create_protocol:
            with patch.object(
                QumuloAPI, "delete_protocol", MagicMock()
            ) as mock_delete_protocol:
                qumulo_instance.update_allocation(
                    protocols=["nfs", "smb"],
                    export_path="/foo",
                    fs_path="/bar",
                    name="bar",
                    limit_in_bytes=10**9,
                )

                create_calls = [
                    call(
                        protocol="nfs", fs_path="/bar", name="bar", export_path="/foo"
                    ),
                    call(
                        protocol="smb", fs_path="/bar", name="bar", export_path="/foo"
                    ),
                ]
                mock_create_protocol.assert_has_calls(create_calls, any_order=True)
                assert mock_create_protocol.call_count == 2

                delete_calls = [call(protocol="s3", name="bar", export_path="/foo")]
                mock_delete_protocol.assert_has_calls(delete_calls, any_order=True)

    def test_catches_request_error_on_delete(self, mock_RestClient: MagicMock):
        def delete_side_effect(protocol, *args, **kwargs):
            if protocol == "s3":
                raise RequestError(404, "Bucket not found")

        qumulo_instance = QumuloAPI()

        with patch.object(
            QumuloAPI, "create_protocol", MagicMock()
        ) as mock_create_protocol:
            with patch.object(
                QumuloAPI, "delete_protocol", MagicMock()
            ) as mock_delete_protocol:
                mock_delete_protocol.side_effect = delete_side_effect
                try:
                    qumulo_instance.update_allocation(
                        protocols=["nfs", "smb"],
                        export_path="/foo",
                        fs_path="/bar",
                        name="bar",
                        limit_in_bytes=10**9,
                    )
                except:
                    self.fail("Did not catch errors!")

    def test_catches_request_error_on_create(self, mock_RestClient: MagicMock):
        def create_side_effect(protocol, *args, **kwargs):
            if protocol in ["nfs", "smb"]:
                raise RequestError(409, "Already exists")

        qumulo_instance = QumuloAPI()

        with patch.object(
            QumuloAPI, "create_protocol", MagicMock()
        ) as mock_create_protocol:
            with patch.object(
                QumuloAPI, "delete_protocol", MagicMock()
            ) as mock_delete_protocol:
                mock_create_protocol.side_effect = create_side_effect
                try:
                    qumulo_instance.update_allocation(
                        protocols=["nfs", "smb"],
                        export_path="/foo",
                        fs_path="/bar",
                        name="bar",
                        limit_in_bytes=10**9,
                    )
                except:
                    self.fail("Did not catch errors!")

    def test_does_not_catch_create_unknown_error(self, mock_RestClient: MagicMock):
        def create_side_effect(protocol, **kwargs):
            if protocol in ["nfs", "smb"]:
                raise Exception()

        def delete_side_effect(protocol, *args, **kwargs):
            if protocol == "s3":
                raise RequestError("pool", "url", "msg")

        qumulo_instance = QumuloAPI()

        with patch.object(
            QumuloAPI, "create_protocol", MagicMock()
        ) as mock_create_protocol:
            with patch.object(
                QumuloAPI, "delete_protocol", MagicMock()
            ) as mock_delete_protocol:
                mock_create_protocol.side_effect = create_side_effect
                mock_delete_protocol.side_effect = delete_side_effect

                with self.assertRaises(Exception):
                    qumulo_instance.update_allocation(
                        protocols=["nfs", "smb"],
                        export_path="/foo",
                        fs_path="/bar",
                        name="bar",
                        limit_in_bytes=10**9,
                    )

    def test_does_not_catch_delete_unknown_error(self, mock_RestClient: MagicMock):
        def create_side_effect(protocol, **kwargs):
            if protocol in ["nfs", "smb"]:
                raise RequestError("pool", "url", "msg")

        def delete_side_effect(protocol, *args, **kwargs):
            if protocol == "s3":
                raise Exception()

        qumulo_instance = QumuloAPI()

        with patch.object(
            QumuloAPI, "create_protocol", MagicMock()
        ) as mock_create_protocol:
            with patch.object(
                QumuloAPI, "delete_protocol", MagicMock()
            ) as mock_delete_protocol:
                mock_create_protocol.side_effect = create_side_effect
                mock_delete_protocol.side_effect = delete_side_effect

                with self.assertRaises(Exception):
                    qumulo_instance.update_allocation(
                        protocols=["nfs", "smb"],
                        export_path="/foo",
                        fs_path="/bar",
                        name="bar",
                        limit_in_bytes=10**9,
                    )

    def test_catches_defined_s3_type_errors(self, mock_RestClient: MagicMock):
        def delete_side_effect(protocol, *args, **kwargs):
            if protocol == "s3":
                raise TypeError("Name is not defined.")

        qumulo_instance = QumuloAPI()

        with patch.object(
            QumuloAPI, "create_protocol", MagicMock()
        ) as mock_create_protocol:
            with patch.object(
                QumuloAPI, "delete_protocol", MagicMock()
            ) as mock_delete_protocol:
                mock_delete_protocol.side_effect = delete_side_effect
                try:
                    qumulo_instance.update_allocation(
                        protocols=["nfs", "smb"],
                        export_path="/foo",
                        fs_path="/bar",
                        name="bar",
                        limit_in_bytes=10**9,
                    )
                except TypeError as e:
                    self.fail("Type Error not catched.")

    def test_catches_defined_nfs_type_errors(self, mock_RestClient: MagicMock):
        def delete_side_effect(protocol, *args, **kwargs):
            if protocol == "nfs":
                raise TypeError("Export path is not defined.")

        qumulo_instance = QumuloAPI()

        with patch.object(
            QumuloAPI, "create_protocol", MagicMock()
        ) as mock_create_protocol:
            with patch.object(
                QumuloAPI, "delete_protocol", MagicMock()
            ) as mock_delete_protocol:
                mock_delete_protocol.side_effect = delete_side_effect
                try:
                    qumulo_instance.update_allocation(
                        protocols=["smb"],
                        export_path="/foo",
                        fs_path="/bar",
                        name="bar",
                        limit_in_bytes=10**9,
                    )
                except TypeError as e:
                    self.fail("Type Error not catched.")

    def test_does_not_catch_not_defined_type_errors(self, mock_RestClient: MagicMock):
        def delete_side_effect(protocol, *args, **kwargs):
            if protocol == "s3":
                raise TypeError()

        qumulo_instance = QumuloAPI()

        with patch.object(
            QumuloAPI, "create_protocol", MagicMock()
        ) as mock_create_protocol:
            with patch.object(
                QumuloAPI, "delete_protocol", MagicMock()
            ) as mock_delete_protocol:
                mock_delete_protocol.side_effect = delete_side_effect
                with self.assertRaises(TypeError):
                    qumulo_instance.update_allocation(
                        protocols=["nfs", "smb"],
                        export_path="/foo",
                        fs_path="/bar",
                        name="bar",
                        limit_in_bytes=10**9,
                    )
