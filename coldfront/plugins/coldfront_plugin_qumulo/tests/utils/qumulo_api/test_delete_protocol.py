from django.test import TestCase
from unittest.mock import patch, MagicMock, PropertyMock
from coldfront_plugin_qumulo.utils.qumulo_api import QumuloAPI


@patch.object(QumuloAPI, "get_id", MagicMock())
@patch("coldfront_plugin_qumulo.utils.qumulo_api.RestClient")
class DeleteProtocol(TestCase):
    def test_gets_nfs_export_id(self, mock_RestClient: MagicMock):
        with patch.object(QumuloAPI, "get_id", MagicMock()) as mock_get_id:
            qumulo_instance = QumuloAPI()
            qumulo_instance.delete_protocol(
                name="foo", protocol="nfs", export_path="bar"
            )

            mock_get_id.assert_called_once_with(protocol="nfs", export_path="bar")

    def test_gets_smb_export_id(self, mock_RestClient: MagicMock):
        with patch.object(QumuloAPI, "get_id", MagicMock()) as mock_get_id:
            qumulo_instance = QumuloAPI()
            qumulo_instance.delete_protocol(
                name="foo", protocol="smb", export_path="bar"
            )

            mock_get_id.assert_called_once_with(protocol="smb", name="foo")

    def test_deletes_nfs_export(self, mock_RestClient: MagicMock):
        mock_nfs = PropertyMock(return_value=MagicMock())
        type(mock_RestClient.return_value).nfs = mock_nfs

        qumulo_instance = QumuloAPI()
        qumulo_instance.delete_protocol(export_path="bar", name="foo", protocol="nfs")

        mock_RestClient.assert_called_once()
        mock_nfs.return_value.nfs_delete_export.assert_called_once()

    def test_deletes_s3_bucket(self, mock_RestClient: MagicMock):
        mock_s3 = PropertyMock(return_value=MagicMock())
        type(mock_RestClient.return_value).s3 = mock_s3

        qumulo_instance = QumuloAPI()
        qumulo_instance.delete_protocol(export_path="bar", name="foo", protocol="s3")

        mock_RestClient.assert_called_once()
        mock_s3.return_value.delete_bucket.assert_called_once()

    def test_deletes_smb_share(self, mock_RestClient: MagicMock):
        mock_smb = PropertyMock(return_value=MagicMock())
        type(mock_RestClient.return_value).smb = mock_smb

        qumulo_instance = QumuloAPI()
        qumulo_instance.delete_protocol(export_path="bar", name="foo", protocol="smb")

        mock_RestClient.assert_called_once()
        mock_smb.return_value.smb_delete_share.assert_called_once()

    def test_rejects_when_incorrect_protocol(self, mock_RestClient: MagicMock):
        qumulo_instance = QumuloAPI()

        with self.assertRaises(ValueError):
            qumulo_instance.delete_protocol(protocol="bad_protocol")

    def test_rejects_when_s3_args_not_defined(self, mock_RestClient: MagicMock):
        qumulo_instance = QumuloAPI()

        with self.assertRaises(TypeError):
            qumulo_instance.delete_protocol(protocol="s3")

    def test_rejects_when_nfs_args_not_defined(self, mock_RestClient: MagicMock):
        qumulo_instance = QumuloAPI()

        with self.assertRaises(TypeError):
            qumulo_instance.delete_protocol(protocol="nfs")

    def test_rejects_when_smb_args_not_defined(self, mock_RestClient: MagicMock):
        qumulo_instance = QumuloAPI()

        with self.assertRaises(TypeError):
            qumulo_instance.delete_protocol(protocol="smb")

    def test_deletes_nfs_with_only_required_params(self, mock_RestClient: MagicMock):
        mock_nfs = PropertyMock(return_value=MagicMock())
        type(mock_RestClient.return_value).nfs = mock_nfs

        qumulo_instance = QumuloAPI()
        qumulo_instance.delete_protocol(export_path="bar", protocol="nfs")

        mock_RestClient.assert_called_once()
        mock_nfs.return_value.nfs_delete_export.assert_called_once()

    def test_deletes_s3_bucket_with_only_required_params(
        self, mock_RestClient: MagicMock
    ):
        mock_s3 = PropertyMock(return_value=MagicMock())
        type(mock_RestClient.return_value).s3 = mock_s3

        qumulo_instance = QumuloAPI()
        qumulo_instance.delete_protocol(name="foo", protocol="s3")

        mock_RestClient.assert_called_once()
        mock_s3.return_value.delete_bucket.assert_called_once()
