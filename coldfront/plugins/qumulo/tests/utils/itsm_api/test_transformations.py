import os

from django.test import TestCase

from unittest import mock

from coldfront.plugins.qumulo.services.itsm.fields.transformers import (
    acl_group_members_to_aggregate_create_users,
    comment_to_protocols,
    fileset_name_to_storage_name,
    fileset_name_to_storage_export_path,
    fileset_name_to_storage_filesystem_path,
    string_parsing_quota_and_unit_to_integer,
    truthy_or_falsy_to_boolean,
)

"""
python manage.py test coldfront.plugins.qumulo.tests.utils.itsm_api.test_transformations
"""
class TestValidators(TestCase):

    def setUp(self) -> None:
        return super().setUp()

    def test_acl_group_members_to_aggregate_create_users(self):
        acl_group_members_from_itsm = (
            "akronzer,derek.harford,d.ken,ehogue,jiaoy,perezm,xuebing"
        )
        result = acl_group_members_from_itsm.split(",")
        self.assertListEqual(
            acl_group_members_to_aggregate_create_users(acl_group_members_from_itsm),
            result,
        )

    def test_comment_to_protocols(self):
        default_protocol_list = ["smb"]
        sample_comment = {"custom_name": "CBMI-Chip", "smb_export_name": "cbmi-chip"}
        self.assertListEqual(
            comment_to_protocols(sample_comment),
            default_protocol_list,
        )

    def test_fileset_name_to_storage_name(self):
        itsm_fileset_name = "jiaoy_active"
        self.assertEqual(fileset_name_to_storage_name(itsm_fileset_name), "jiaoy")

        itsm_fileset_alias = "gc6159"
        self.assertEqual(fileset_name_to_storage_name(itsm_fileset_alias), "gc6159")

        itsm_fileset_name_bad = "jiaoy_archive"
        self.assertNotEqual(
            fileset_name_to_storage_name(itsm_fileset_name_bad), "jiaoy"
        )

    @mock.patch.dict(os.environ, {"STORAGE2_PATH": "/storage2-test"})
    def test_fileset_name_to_storage_export_path(self):
        itsm_fileset_name = "jiaoy_active"
        self.assertEqual(
            fileset_name_to_storage_export_path(itsm_fileset_name),
            "/storage2-test/jiaoy",
        )

        itsm_fileset_alias = "gc6159"
        self.assertEqual(
            fileset_name_to_storage_export_path(itsm_fileset_alias),
            "/storage2-test/gc6159",
        )

    @mock.patch.dict(os.environ, {"STORAGE2_PATH": "/storage2-test"})
    def test_fileset_name_to_storage_filesystem_path(self):
        itsm_fileset_name = "jiaoy_active"
        self.assertEqual(
            fileset_name_to_storage_filesystem_path(itsm_fileset_name),
            "/storage2-test/jiaoy",
        )

        itsm_fileset_alias = "gc6159"
        self.assertEqual(
            fileset_name_to_storage_filesystem_path(itsm_fileset_alias),
            "/storage2-test/gc6159",
        )

    def test_string_parsing_quota_and_unit_to_integer(self):
        self.assertEquals(string_parsing_quota_and_unit_to_integer("80T"), 80)
        self.assertEquals(string_parsing_quota_and_unit_to_integer("500G"), 1)
        self.assertEquals(string_parsing_quota_and_unit_to_integer("1500G"), 2)

        for bad_value in ["80", "80bogus", None]:
            message = f'The quota "{bad_value}" is not valid. The unit is not T (for TB) or G (for GB), or it is missing.'
            self.assertRaises(
                Exception,
                string_parsing_quota_and_unit_to_integer,
                bad_value,
                msg=message,
            )

    def test_truthy_or_falsy_to_boolean(self):
        self.assertTrue(truthy_or_falsy_to_boolean("True"))
        self.assertTrue(truthy_or_falsy_to_boolean("true"))
        self.assertTrue(truthy_or_falsy_to_boolean("1"))
        self.assertTrue(truthy_or_falsy_to_boolean(1))
        self.assertTrue(truthy_or_falsy_to_boolean(True))

        self.assertFalse(truthy_or_falsy_to_boolean("False"))
        self.assertFalse(truthy_or_falsy_to_boolean("false"))
        self.assertFalse(truthy_or_falsy_to_boolean("0"))
        self.assertFalse(truthy_or_falsy_to_boolean(0))
        self.assertFalse(truthy_or_falsy_to_boolean(False))

        self.assertIsNone(truthy_or_falsy_to_boolean(None))
        defaults_to = True
        self.assertIsNotNone(truthy_or_falsy_to_boolean(None, defaults_to))
        defaults_to = False
        self.assertIsNotNone(truthy_or_falsy_to_boolean(None, defaults_to))
        self.assertRaises(ValueError, truthy_or_falsy_to_boolean, "Bogus Data")


"""
python manage.py test coldfront.plugins.qumulo.tests.utils.itsm_api.test_validators

from coldfront.plugins.qumulo.services.itsm.fields.validators import numericallity
coldfront/plugins/qumulo/tests/utils.itsm_api.test_validators
"""


# comment_to_read_only_users
# comment_to_read_write_users
# from comments, dir_projects are sub allocations
# from comments, if smb_export_name include smb in the protocols
# fileset_name_to_storage_filesystem_path
# fileset_name_to_storage_export_path


"""
    allocation_attribute_names = [
        "storage_name",
        "storage_quota",
        "storage_protocols",
        "storage_filesystem_path",
        "storage_export_path",
        "department_number",
        "cost_center",
        "service_rate",
        "storage_ticket",
        "technical_contact",
        "billing_contact",
    ]

        form_data = {
            "storage_filesystem_path": path, DONE
            "storage_export_path": path, DONE
            "storage_name": f"for_tester_{index}", DONE
            "storage_quota": limit, DONE
            "protocols": ["nfs"], DONE
            "rw_users": [f"user_{index}_rw"],
            "ro_users": [f"user_{index}_ro"],
            "storage_ticket": f"ITSD-{index}", DONE
            "cost_center": "Uncle Pennybags", DONE
            "department_number": "Time Travel Services", DONE
            "service_rate": "general", DONE
        }
"""
