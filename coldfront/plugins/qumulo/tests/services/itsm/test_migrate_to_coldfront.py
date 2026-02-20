import json
from django.test import TestCase

from unittest import mock
from unittest.mock import MagicMock, patch

from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttribute,
)
from coldfront.core.project.models import Project, ProjectAttribute

from coldfront.plugins.qumulo.services.itsm.migrate_to_coldfront import (
    MigrateToColdfront,
)
from coldfront.plugins.qumulo.tests.fixtures import create_metadata_for_testing
from coldfront.plugins.qumulo.tests.helper_classes.filesystem_path import (
    ValidFormPathMock,
)
from coldfront.plugins.qumulo.tests.utils.mock_data import mock_qumulo_info

QUMULO_INFO = mock_qumulo_info
storage2_path = QUMULO_INFO["Storage2"]["path"]


def ad_lookup_get_user_side_effect(value: str):
    if value != "no-exist":
        return {"dn": "user_dn", "attributes": {"other_attr": "value"}}
    else:
        raise ValueError("User not found")


@patch.dict("os.environ", {"QUMULO_INFO": json.dumps(QUMULO_INFO)})
@mock.patch(
    "coldfront.plugins.qumulo.services.itsm.fields.validators.ActiveDirectoryAPI"
)
@mock.patch("coldfront.plugins.qumulo.services.itsm.migrate_to_coldfront.ItsmClient")
@mock.patch("coldfront.plugins.qumulo.services.allocation_service.ActiveDirectoryAPI")
@mock.patch("coldfront.plugins.qumulo.services.allocation_service.async_task")
class TestMigrateToColdfront(TestCase):

    def setUp(self) -> None:
        create_metadata_for_testing()
        self.mock_factory = patch(
            "coldfront.plugins.qumulo.validators.StorageControllerFactory"
        ).start()

        self.mock_qumulo_api = MagicMock()
        self.mock_factory.return_value.create_connection.return_value = (
            self.mock_qumulo_api
        )

        self.expected_allocation_attributes = [
            ("storage_name", "mocker"),
            ("storage_quota", "200"),
            ("storage_protocols", '["smb"]'),
            ("storage_filesystem_path", f"{storage2_path}/mocker"),
            ("storage_export_path", f"{storage2_path}/mocker"),
            ("cost_center", "CC0004259"),
            ("department_number", "CH00409"),
            ("service_rate_category", "consumption"),
            ("secure", "No"),
            ("audit", "No"),
            ("billing_exempt", "No"),
            ("subsidized", "Yes"),
            ("billing_contact", "jin810"),
            ("technical_contact", "jin810"),
            ("storage_ticket", "ITSD-2222"),
            ("billing_startdate", "2020-04-15T00: 00: 00.000Z"),
            ("fileset_name", "mocker_active"),
            ("fileset_alias", "mocker_active"),
            (
                "itsm_comment",
                '{"afm_cache_enable":true,"_jenkins":"https://systems-ci.gsc.wustl.edu/job/storage1_allocation/2652","add_archive":"true"}',
            ),
            ("billing_cycle", "monthly"),
            ("sla_name", ""),
        ]

        self.expected_allocation_attributes_missing_contacts = [
            ("storage_name", "mocker_missing_contacts"),
            ("storage_quota", "200"),
            ("storage_protocols", '["smb"]'),
            ("storage_filesystem_path", f"{storage2_path}/mocker_missing_contacts"),
            ("storage_export_path", f"{storage2_path}/mocker_missing_contacts"),
            ("cost_center", "CC0004259"),
            ("department_number", "CH00409"),
            ("service_rate_category", "consumption"),
            ("secure", "No"),
            ("audit", "No"),
            ("billing_exempt", "No"),
            ("subsidized", "Yes"),
            ("storage_ticket", "ITSD-2222"),
            ("billing_startdate", "2020-04-15T00: 00: 00.000Z"),
            ("fileset_name", "mocker_missing_contacts_active"),
            ("fileset_alias", "mocker_missing_contacts_active"),
            (
                "itsm_comment",
                '{"afm_cache_enable":true,"_jenkins":"https://systems-ci.gsc.wustl.edu/job/storage1_allocation/2652","add_archive":"true"}',
            ),
            ("billing_cycle", "monthly"),
            ("sla_name", ""),
        ]

        self.expected_allocation_attributes_billing_startdate_missing = [
            ("storage_name", "mocker"),
            ("storage_quota", "200"),
            ("storage_protocols", '["smb"]'),
            ("storage_filesystem_path", f"{storage2_path}/mocker"),
            ("storage_export_path", f"{storage2_path}/mocker"),
            ("cost_center", "CC0004259"),
            ("department_number", "CH00409"),
            ("service_rate_category", "consumption"),
            ("secure", "No"),
            ("audit", "No"),
            ("billing_exempt", "No"),
            ("subsidized", "Yes"),
            ("billing_contact", "jin810"),
            ("technical_contact", "jin810"),
            ("storage_ticket", "ITSD-2222"),
            ("fileset_name", "mocker_active"),
            ("fileset_alias", "mocker_active"),
            (
                "itsm_comment",
                '{"afm_cache_enable":true,"_jenkins":"https://systems-ci.gsc.wustl.edu/job/storage1_allocation/2652","add_archive":"true"}',
            ),
            ("billing_cycle", "monthly"),
            ("sla_name", ""),
        ]

        self.expected_allocation_attributes_itsm_comment_missing = [
            ("storage_name", "mocker"),
            ("storage_quota", "200"),
            ("storage_protocols", '["smb"]'),
            ("storage_filesystem_path", f"{storage2_path}/mocker"),
            ("storage_export_path", f"{storage2_path}/mocker"),
            ("cost_center", "CC0004259"),
            ("department_number", "CH00409"),
            ("service_rate_category", "consumption"),
            ("secure", "No"),
            ("audit", "No"),
            ("billing_exempt", "No"),
            ("subsidized", "Yes"),
            ("billing_contact", "jin810"),
            ("technical_contact", "jin810"),
            ("storage_ticket", "ITSD-2222"),
            ("fileset_name", "mocker_active"),
            ("fileset_alias", "mocker_active"),
            ("billing_cycle", "monthly"),
            ("sla_name", ""),
        ]

        self.expected_allocation_attributes_itsm_comment_dir_projects = [
            ("storage_name", "jin810"),
            ("storage_quota", "200"),
            ("storage_protocols", '["smb"]'),
            ("storage_filesystem_path", f"{storage2_path}/jin810"),
            ("storage_export_path", f"{storage2_path}/jin810"),
            ("cost_center", "CC0004259"),
            ("department_number", "CH00409"),
            ("service_rate_category", "consumption"),
            ("secure", "No"),
            ("audit", "No"),
            ("billing_exempt", "No"),
            ("subsidized", "Yes"),
            ("billing_contact", "jin810"),
            ("technical_contact", "jin810"),
            ("storage_ticket", "ITSD-2222"),
            ("fileset_name", "jin810_active"),
            ("fileset_alias", "jin810_active"),
            ("billing_cycle", "monthly"),
            ("sla_name", ""),
            (
                "itsm_comment",
                '{"dir_projects":{"KHADER":{"ro":null,"rw":null},"KHADER_ADMIN":{"ro":null,"rw":["mushtaqahmed","pamelacamp"]},"KHADERLAB_PROTOCOLS":{"ro":["akter","bobba.suhas","chauhank","darya.urusova","lmellett","lulan","ncaleb","rswanson","s.thirunavukkarasu","sbmehta","yangyan"],"rw":["g.ananya","mushtaqahmed","shibalidas"]},"KHADERLAB_TBPROGRAM":{"ro":null,"rw":["akter","bobba.suhas","chauhank","darya.urusova","g.ananya","lmellett","lulan","mushtaqahmed","ncaleb","pamelacamp","rswanson","s.thirunavukkarasu","sbmehta","shibalidas","yangyan"]},"PAPER_2018":{"ro":null,"rw":["shibalidas"]},"Khader_lab":{"ro":null,"rw":["jmartin"]},"Khadercompute":{"ro":null,"rw":["akter","bobba.suhas","jmartin","mushtaqahmed","sakhader"]},"Shared_With_Max":{"ro":null,"rw":["akter","mushtaqahmed","shibalidas","storage-martyomov"]},"MGI_Data":{"rw":["barosa","jmartin","storage-sakhader-khaderlab_tbprogram-rw"],"ro":[]}}}',
            ),
        ]

    def tearDown(self):
        patch.stopall()
        return super().tearDown()

    def test_migrate_to_coldfront_by_fileset_name(
        self,
        mock_async_task: mock.MagicMock,
        mock_active_directory_api: mock.MagicMock,
        mock_itsm_client: mock.MagicMock,
        mock_ad_api_in_validator: mock.MagicMock,
    ) -> None:
        with open(
            "coldfront/plugins/qumulo/static/migration_mappings/mock_itsm_response_body_service_provision_found.json",
            "r",
        ) as file:
            mock_response = json.load(file)["data"]
            itsm_client = mock.MagicMock()
            itsm_client.get_fs1_allocation_by_fileset_name.return_value = mock_response
            mock_itsm_client.return_value = itsm_client

        mock_ad_api_in_validator.get_user.side_effect = ad_lookup_get_user_side_effect
        self.mock_qumulo_api.rc.fs.get_file_attr = ValidFormPathMock()

        name = "mocker"
        result = MigrateToColdfront().by_fileset_name(f"{name}_active", "Storage2")
        self.assertDictEqual(
            result,
            {
                "allocation_id": 1,
                "pi_user_id": 1,
                "project_id": 1,
                "warning_messages": {},
            },
        )

        allocation = Allocation.objects.get(id=result["allocation_id"])
        project = Project.objects.get(id=result["project_id"])
        self.assertEqual(allocation.id, result["allocation_id"])
        self.assertEqual(allocation.project, project)
        self.assertEqual(allocation.project.title, "jin810")

        allocation_attributes = AllocationAttribute.objects.filter(
            allocation=result["allocation_id"]
        )
        allocation_attribute_values = allocation_attributes.values_list(
            "allocation_attribute_type__name", "value"
        )

        for attribute_value in self.expected_allocation_attributes:
            self.assertIn(attribute_value, allocation_attribute_values)

        self.assertEqual(allocation_attributes.count(), 21)

        project_attributes = ProjectAttribute.objects.filter(
            project=result["project_id"]
        )
        self.assertEqual(len(project_attributes), 3)

    def test_migrate_to_coldfront_by_service_provision_name(
        self,
        mock_async_task: mock.MagicMock,
        mock_active_directory_api: mock.MagicMock,
        mock_itsm_client: mock.MagicMock,
        mock_ad_api_in_validator: mock.MagicMock,
    ) -> None:
        with open(
            "coldfront/plugins/qumulo/static/migration_mappings/mock_itsm_response_body_service_provision_found.json",
            "r",
        ) as file:
            mock_response = json.load(file)["data"]
            itsm_client = mock.MagicMock()
            itsm_client.get_fs1_allocation_by_storage_provision_name.return_value = (
                mock_response
            )
            mock_itsm_client.return_value = itsm_client

        mock_ad_api_in_validator.get_user.side_effect = ad_lookup_get_user_side_effect
        self.mock_qumulo_api.rc.fs.get_file_attr = ValidFormPathMock()

        name = "mocker"
        result = MigrateToColdfront().by_storage_provision_name(f"{name}", "Storage2")
        self.assertDictEqual(
            result,
            {
                "allocation_id": 1,
                "pi_user_id": 1,
                "project_id": 1,
                "warning_messages": {},
            },
        )

        allocation = Allocation.objects.get(id=result["allocation_id"])
        project = Project.objects.get(id=result["project_id"])
        self.assertEqual(allocation.id, result["allocation_id"])
        self.assertEqual(allocation.project, project)
        self.assertEqual(allocation.project.title, "jin810")

        allocation_attributes = AllocationAttribute.objects.filter(
            allocation=result["allocation_id"]
        )
        allocation_attribute_values = allocation_attributes.values_list(
            "allocation_attribute_type__name", "value"
        )

        for attribute_value in self.expected_allocation_attributes:
            self.assertIn(attribute_value, allocation_attribute_values)

        self.assertEqual(allocation_attributes.count(), 21)

        project_attributes = ProjectAttribute.objects.filter(
            project=result["project_id"]
        )
        self.assertEqual(len(project_attributes), 3)

    def test_migrate_to_coldfront_by_fileset_alias(
        self,
        mock_async_task: mock.MagicMock,
        mock_active_directory_api: mock.MagicMock,
        mock_itsm_client: mock.MagicMock,
        mock_ad_api_in_validator: mock.MagicMock,
    ) -> None:
        with open(
            "coldfront/plugins/qumulo/static/migration_mappings/mock_itsm_response_body_service_provision_found.json",
            "r",
        ) as file:
            mock_response = json.load(file)["data"]
            itsm_client = mock.MagicMock()
            itsm_client.get_fs1_allocation_by_fileset_alias.return_value = mock_response
            mock_itsm_client.return_value = itsm_client

        mock_ad_api_in_validator.get_user.side_effect = ad_lookup_get_user_side_effect
        self.mock_qumulo_api.rc.fs.get_file_attr = ValidFormPathMock()

        fileset_alias = "mocker_active"
        name = "mocker"
        result = MigrateToColdfront().by_fileset_alias(f"{fileset_alias}", "Storage2")
        self.assertDictEqual(
            result,
            {
                "allocation_id": 1,
                "pi_user_id": 1,
                "project_id": 1,
                "warning_messages": {},
            },
        )

        allocation = Allocation.objects.get(id=result["allocation_id"])
        project = Project.objects.get(id=result["project_id"])
        self.assertEqual(allocation.id, result["allocation_id"])
        self.assertEqual(allocation.project, project)
        self.assertEqual(allocation.project.title, "jin810")

        allocation_attributes = AllocationAttribute.objects.filter(
            allocation=result["allocation_id"]
        )
        allocation_attribute_values = allocation_attributes.values_list(
            "allocation_attribute_type__name", "value"
        )

        for attribute_value in self.expected_allocation_attributes:
            self.assertIn(attribute_value, allocation_attribute_values)

        self.assertEqual(allocation_attributes.count(), 21)

        project_attributes = ProjectAttribute.objects.filter(
            project=result["project_id"]
        )
        self.assertEqual(len(project_attributes), 3)

    def test_migrate_to_coldfront_with_contacts_missing(
        self,
        mock_async_task: mock.MagicMock,
        mock_active_directory_api: mock.MagicMock,
        mock_itsm_client: mock.MagicMock,
        mock_ad_api_in_validator: mock.MagicMock,
    ) -> None:
        with open(
            "coldfront/plugins/qumulo/static/migration_mappings/mock_itsm_response_body_service_provision_found_missing_contacts.json",
            "r",
        ) as file:
            mock_response = json.load(file)["data"]
            itsm_client = mock.MagicMock()
            itsm_client.get_fs1_allocation_by_fileset_name.return_value = mock_response
            mock_itsm_client.return_value = itsm_client

        mock_ad_api_in_validator.get_user.side_effect = ad_lookup_get_user_side_effect
        self.mock_qumulo_api.rc.fs.get_file_attr = ValidFormPathMock()

        name = "mocker_missing_contacts"

        self.assertRaises(
            Exception,
            MigrateToColdfront().by_fileset_name,
            f"{name}_active",
            "Storage2",
            msg="{'errors': {'sponsor': ['mocker_missing_contacts does not exist in Active Directory']}, 'warnings': {}}",
        )

    def test_migrate_to_coldfront_with_billing_startdate_missing(
        self,
        mock_async_task: mock.MagicMock,
        mock_active_directory_api: mock.MagicMock,
        mock_itsm_client: mock.MagicMock,
        mock_ad_api_in_validator: mock.MagicMock,
    ) -> None:
        with open(
            "coldfront/plugins/qumulo/static/migration_mappings/mock_itsm_response_body_billing_startdate_not_found.json",
            "r",
        ) as file:
            mock_response = json.load(file)["data"]
            itsm_client = mock.MagicMock()
            itsm_client.get_fs1_allocation_by_fileset_name.return_value = mock_response
            mock_itsm_client.return_value = itsm_client

        mock_ad_api_in_validator.get_user.side_effect = ad_lookup_get_user_side_effect
        self.mock_qumulo_api.rc.fs.get_file_attr = ValidFormPathMock()

        name = "mocker"
        result = MigrateToColdfront().by_fileset_name(f"{name}_active", "Storage2")
        allocation = Allocation.objects.get(id=result["allocation_id"])
        self.assertEqual(allocation.id, result["allocation_id"])

        allocation_attributes = AllocationAttribute.objects.filter(
            allocation=result["allocation_id"]
        )
        allocation_attribute_values = allocation_attributes.values_list(
            "allocation_attribute_type__name", "value"
        )

        for (
            attribute_value
        ) in self.expected_allocation_attributes_billing_startdate_missing:
            self.assertIn(attribute_value, allocation_attribute_values)

        self.assertEqual(allocation_attributes.count(), 20)
        # optional fields with empty or missing values should not create
        # allocation_attributes on create allocation
        for value in [("billing_startdate", "")]:
            self.assertNotIn(value, allocation_attribute_values)

    def test_migrate_to_coldfront_with_itsm_comment_missing(
        self,
        mock_async_task: mock.MagicMock,
        mock_active_directory_api: mock.MagicMock,
        mock_itsm_client: mock.MagicMock,
        mock_ad_api_in_validator: mock.MagicMock,
    ) -> None:
        with open(
            "coldfront/plugins/qumulo/static/migration_mappings/mock_itsm_response_body_service_provision_found_itsm_comment_empty.json",
            "r",
        ) as file:
            mock_response = json.load(file)["data"]
            itsm_client = mock.MagicMock()
            itsm_client.get_fs1_allocation_by_fileset_name.return_value = mock_response
            mock_itsm_client.return_value = itsm_client

        mock_ad_api_in_validator.get_user.side_effect = ad_lookup_get_user_side_effect
        self.mock_qumulo_api.rc.fs.get_file_attr = ValidFormPathMock()

        name = "mocker"
        result = MigrateToColdfront().by_fileset_name(f"{name}_active", "Storage2")
        allocation = Allocation.objects.get(id=result["allocation_id"])
        self.assertEqual(allocation.id, result["allocation_id"])

        allocation_attributes = AllocationAttribute.objects.filter(
            allocation=result["allocation_id"]
        )
        allocation_attribute_values = allocation_attributes.values_list(
            "allocation_attribute_type__name", "value"
        )

        for attribute_value in self.expected_allocation_attributes_itsm_comment_missing:
            self.assertIn(attribute_value, allocation_attribute_values)

        self.assertEqual(allocation_attributes.count(), 21)
        # optional fields with empty or missing values should not create
        # allocation_attributes on create allocation
        for value in [("itsm_comment", None)]:
            self.assertNotIn(value, allocation_attribute_values)

    def test_migrate_to_coldfront_with_itsm_comment_dir_projects(
        self,
        mock_async_task: mock.MagicMock,
        mock_active_directory_api: mock.MagicMock,
        mock_itsm_client: mock.MagicMock,
        mock_ad_api_in_validator: mock.MagicMock,
    ) -> None:
        with open(
            "coldfront/plugins/qumulo/static/migration_mappings/mock_itsm_response_body_service_provision_found_itsm_comment_dir_projects.json",
            "r",
        ) as file:
            mock_response = json.load(file)["data"]
            itsm_client = mock.MagicMock()
            itsm_client.get_fs1_allocation_by_fileset_name.return_value = mock_response
            mock_itsm_client.return_value = itsm_client

        mock_ad_api_in_validator.get_user.side_effect = ad_lookup_get_user_side_effect
        self.mock_qumulo_api.rc.fs.get_file_attr = ValidFormPathMock()

        name = "jin810"
        result = MigrateToColdfront().by_fileset_name(f"{name}_active", "Storage2")
        allocation = Allocation.objects.get(id=result["allocation_id"])
        self.assertEqual(allocation.id, result["allocation_id"])

        allocation_attributes = AllocationAttribute.objects.filter(
            allocation=result["allocation_id"]
        )
        allocation_attribute_values = allocation_attributes.values_list(
            "allocation_attribute_type__name", "value"
        )

        for (
            attribute_value
        ) in self.expected_allocation_attributes_itsm_comment_dir_projects:
            if attribute_value[0] == "itsm_comment":
                self.assertDictEqual(
                    json.loads(
                        allocation_attribute_values.get(
                            allocation_attribute_type__name="itsm_comment"
                        )[1]
                    ),
                    json.loads(attribute_value[1]),
                )
                continue
            self.assertIn(attribute_value, allocation_attribute_values)

        self.assertEqual(allocation_attributes.count(), 21)

    def test_migrate_to_coldfront_with_itsm_comment_dir_projects_with_errors_and_warnings(
        self,
        mock_async_task: mock.MagicMock,
        mock_active_directory_api: mock.MagicMock,
        mock_itsm_client: mock.MagicMock,
        mock_ad_api_in_validator: mock.MagicMock,
    ) -> None:
        with open(
            "coldfront/plugins/qumulo/static/migration_mappings/mock_itsm_response_body_service_provision_found_itsm_comment_dir_projects_with_errors_and_warnings.json",
            "r",
        ) as file:
            mock_response = json.load(file)["data"]
            itsm_client = mock.MagicMock()
            itsm_client.get_fs1_allocation_by_fileset_name.return_value = mock_response
            mock_itsm_client.return_value = itsm_client
        mock_ad_api_in_validator.get_user.side_effect = ad_lookup_get_user_side_effect

        name = "jin810"
        self.assertRaises(
            Exception,
            MigrateToColdfront().by_fileset_name,
            f"{name}_active",
            "Storage2",
            msg="{'errors': {'comment': [['sub-allocation name KHADER ADMIN is invalid']]}, 'warnings': {'acl_group_members': [['no-exist does not exist in Active Directory']]}}",
        )

    def test_migrate_to_coldfront_by_fileset_name_override_ticket_number(
        self,
        mock_async_task: mock.MagicMock,
        mock_active_directory_api: mock.MagicMock,
        mock_itsm_client: mock.MagicMock,
        mock_ad_api_in_validator: mock.MagicMock,
    ) -> None:
        with open(
            "coldfront/plugins/qumulo/static/migration_mappings/mock_itsm_response_body_service_provision_found.json",
            "r",
        ) as file:
            mock_response = json.load(file)["data"]
            itsm_client = mock.MagicMock()
            itsm_client.get_fs1_allocation_by_fileset_name.return_value = mock_response
            mock_itsm_client.return_value = itsm_client

        mock_ad_api_in_validator.get_user.side_effect = ad_lookup_get_user_side_effect
        self.mock_qumulo_api.rc.fs.get_file_attr = ValidFormPathMock()

        name = "jin810"
        ticket_number_override = "ITSD-54321"
        migrate = MigrateToColdfront()
        migrate.set_override("service_desk_ticket_number", ticket_number_override)
        result = migrate.by_fileset_name(f"{name}_active", "Storage2")

        ticket_number_allocation_attribute_value = AllocationAttribute.objects.get(
            allocation=result["allocation_id"],
            allocation_attribute_type__name="storage_ticket",
        ).value
        self.assertEqual(
            ticket_number_allocation_attribute_value, ticket_number_override
        )
