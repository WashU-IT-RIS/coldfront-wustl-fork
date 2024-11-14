import os

from django.test import TestCase, tag

from unittest import mock

from coldfront.plugins.qumulo.services.itsm.itsm_client import ItsmClient


class TestItsmClient(TestCase):

    def setUp(self) -> None:
        self.itsm_client = ItsmClient()

    @mock.patch.dict(os.environ, {"QUMULO_RESULT_SET_PAGE_LIMIT": "2000"})
    @tag("integration")
    def test_itsm_client_when_service_provision_is_found_by_fileset_name(self):
        itsm_client = self.itsm_client
        service_provision = itsm_client.get_fs1_allocation_by_fileset_name("jin810_active")
        

    @tag("integration")
    def test_itsm_client_when_service_provision_is_not_found_by_fileset_name(self):
        itsm_client = self.itsm_client
        empty_list = []
        self.assertListEqual(itsm_client.get_fs1_allocation_by_fileset_name("not_going_to_be_found"), empty_list)
        self.assertListEqual(itsm_client.get_fs1_allocation_by_fileset_name(None), empty_list)

    @tag("integration")
    def test_itsm_client_when_the_fileset_name_is_missing(self):
        itsm_client = self.itsm_client
        self.assertRaises(TypeError, itsm_client.get_fs1_allocation_by_fileset_name)
        # TypeError: get_fs1_allocation_by_fileset_name() missing 1 required positional argument: 'fileset_name'


    @tag("integration")
    def test_itsm_client_when_service_provision_is_found_by_fileset_alias(self):
        itsm_client = self.itsm_client
        empty_list = []
        service_provision = itsm_client.get_fs1_allocation_by_fileset_alias("halllab")
        self.assertIsNot(service_provision, empty_list)
        

    @tag("integration")
    def test_itsm_client_when_service_provision_is_not_found_by_fileset_alias(self):
        itsm_client = self.itsm_client
        empty_list = []
        self.assertListEqual(itsm_client.get_fs1_allocation_by_fileset_alias("not_going_to_be_found"), empty_list)
        self.assertListEqual(itsm_client.get_fs1_allocation_by_fileset_alias(None), empty_list)


    @tag("integration")
    def test_itsm_client_when_the_fileset_alias_is_missing(self):
        itsm_client = self.itsm_client
        self.assertRaises(TypeError, itsm_client.get_fs1_allocation_by_fileset_alias)
        # TypeError: get_fs1_allocation_by_fileset_alias() missing 1 required positional argument: 'fileset_alias'
