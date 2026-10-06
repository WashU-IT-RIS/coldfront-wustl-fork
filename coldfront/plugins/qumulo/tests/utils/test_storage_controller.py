import unittest
from unittest.mock import patch

from coldfront.plugins.qumulo.utils.storage_controller import StorageControllerFactory


class MockClass:
    def __init__(self, *args, **kwargs):
        pass


@patch("coldfront.plugins.qumulo.utils.storage_controller.QumuloAPI", new=MockClass)
class TestStorageControllerFactory(unittest.TestCase):
    def test_initialization(self):
        factory = StorageControllerFactory()
        self.assertIsInstance(factory, StorageControllerFactory)

    @unittest.skip("Skipping test for Storage2 connection. Domain knowledge unnecessary for this test. Fix by mocking the qumulo_info.")
    def test_create_connection_storage2(self):
        factory = StorageControllerFactory()
        resource = "Storage2"
        connection = factory.create_connection(resource)

        self.assertIsInstance(connection, MockClass)

    @unittest.skip("Skipping test for Storage3 connection. Domain knowledge unnecessary for this test. Fix by mocking the qumulo_info.")
    def test_create_connection_storage3(self):
        factory = StorageControllerFactory()
        resource = "Storage3"
        connection = factory.create_connection(resource)

        self.assertIsInstance(connection, MockClass)
