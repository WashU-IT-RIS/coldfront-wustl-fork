import json
import os
from unittest.mock import patch
from django.test import TestCase

from coldfront.plugins.qumulo.tests.fixtures import create_ris_resources
from coldfront.plugins.qumulo.tests.utils.mock_data import (
    mock_qumulo_info,
)
from coldfront.plugins.qumulo.forms.TriggerMigrationsForm import (
    TriggerMigrationsForm,
)


@patch.dict(os.environ, {"QUMULO_INFO": json.dumps(mock_qumulo_info)})
class TriggerMigrationFormTests(TestCase):

    def setUp(self):
        create_ris_resources()
        self.DEFAULT_STORAGE_TYPE = "Storage3"
        self.OTHER_STORAGE_TYPE = "Storage2"
        return super().setUp()

    def test_trigger_migration_form_initial_values(self):

        form = TriggerMigrationsForm()
        self.assertEqual(
            form.fields["allocation_resource_name"].initial,
            self.DEFAULT_STORAGE_TYPE,
            msg=f"Initial storage type should be '{self.DEFAULT_STORAGE_TYPE}'",
        )
        self.assertIn(
            (
                self.DEFAULT_STORAGE_TYPE,
                self.DEFAULT_STORAGE_TYPE,
            ),
            form.fields["allocation_resource_name"].choices,
        )
        self.assertIn(
            (
                self.OTHER_STORAGE_TYPE,
                self.OTHER_STORAGE_TYPE,
            ),
            form.fields["allocation_resource_name"].choices,
        )

    def test_trigger_migration_form_validation(self):

        valid_data = {
            "allocation_name_search": "/vol/rdcw-fs1/kchoi",
            "allocation_resource_name": self.DEFAULT_STORAGE_TYPE,
        }
        form = TriggerMigrationsForm(data=valid_data)
        self.assertTrue(form.is_valid(), msg="Form should be valid with correct data")

        invalid_data = {
            "allocation_name_search": "",  # not answered
            "allocation_resource_name": self.DEFAULT_STORAGE_TYPE,
        }
        form = TriggerMigrationsForm(data=invalid_data)
        self.assertFalse(
            form.is_valid(), msg="Form should be invalid with incorrect allocation name"
        )

        self.assertIn(
            "allocation_name_search",
            form.errors,
            msg="Form errors should include allocation_name_search field",
        )
        self.assertEqual(
            form.errors["allocation_name_search"],
            ["This field is required."],
            msg="Error message should indicate invalid value",
        )

    def test_trigger_migration_form_missing_fields(self):

        missing_allocation_name_data = {
            "allocation_resource_name": self.DEFAULT_STORAGE_TYPE,
        }
        form = TriggerMigrationsForm(data=missing_allocation_name_data)
        self.assertFalse(
            form.is_valid(),
            msg="Form should be invalid when allocation_name_search is missing",
        )
        self.assertIn(
            "allocation_name_search",
            form.errors,
            msg="Form errors should include allocation_name_search field",
        )

        missing_resource_name_data = {
            "allocation_name_search": "/vol/rdcw-fs1/kchoi",
        }
        form = TriggerMigrationsForm(data=missing_resource_name_data)
        self.assertFalse(
            form.is_valid(),
            msg="Form should be invalid when allocation_resource_name is missing",
        )
        self.assertIn(
            "allocation_resource_name",
            form.errors,
            msg="Form errors should include allocation_resource_name field",
        )

    def test_trigger_migration_form_invalid_resource(self):

        invalid_resource_data = {
            "allocation_name_search": "/vol/rdcw-fs1/kchoi",
            "allocation_resource_name": "NonExistentResource",
        }
        form = TriggerMigrationsForm(data=invalid_resource_data)
        self.assertFalse(
            form.is_valid(),
            msg="Form should be invalid with non-existent resource name",
        )
        self.assertIn(
            "allocation_resource_name",
            form.errors,
            msg="Form errors should include allocation_resource_name field",
        )
        self.assertEqual(
            form.errors["allocation_resource_name"],
            [
                "Select a valid choice. NonExistentResource is not one of the available choices."
            ],
            msg="Error message should indicate invalid choice",
        )
