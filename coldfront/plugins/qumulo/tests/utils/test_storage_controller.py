import unittest, json, os
from unittest.mock import patch, MagicMock
from coldfront.plugins.qumulo.utils.storage_controller import StorageControllerFactory
from coldfront.plugins.qumulo.utils.qumulo_api import QumuloAPI


class TestStorageControllerFactory(unittest.TestCase):

    def test_initialization(self):
        factory = StorageControllerFactory()
        self.assertIsInstance(factory, StorageControllerFactory)

    def test_create_connection_storage2(self):
        factory = StorageControllerFactory()
        resource = "Storage2"
        connection = factory.create_connection(resource)
        self.assertIsInstance(connection, QumuloAPI)

    def test_create_connection_storage3(self):
        factory = StorageControllerFactory()
        resource = "Storage3"
        connection = factory.create_connection(resource)
        from coldfront.plugins.qumulo.utils.storage_controller import (
            StorageControllerFactory,
        )

        self.assertIsInstance(
            connection, StorageControllerFactory().create_connection("Storage2")
        )
