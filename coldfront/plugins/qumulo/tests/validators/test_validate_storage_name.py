from django.test import TestCase

from coldfront.plugins.qumulo.tests.fixtures import (
    create_allocation_attribute,
    create_attribute_types_for_ris_allocations,
)
from coldfront.plugins.qumulo.tests.helper_classes.factories import (
    Storage2Factory,
    Storage3Factory,
)
from coldfront.plugins.qumulo.validators import (
    validate_storage_name,
    validate_uniqueness_storage_name_for_storage_type,
)
from coldfront.plugins.qumulo.tests.utils.mock_data import build_models

from django.core.exceptions import ValidationError


class TestValidateStorageName(TestCase):
    def setUp(self):
        create_attribute_types_for_ris_allocations()

    def test_accepts_valid_characters(self):
        try:
            validate_storage_name("test-name_123.test")
        except Exception:
            self.fail()

    def test_rejects_invalid_characters(self):
        invalid_chars = [
            " ",
            "!",
            "@",
            "#",
            "$",
            "%",
            "^",
            "&",
            "*",
            "(",
            ")",
            "+",
            "=",
            "[",
            "]",
            "{",
            "}",
            ";",
            ":",
            "'",
            '"',
            "<",
            ">",
            ",",
            "?",
            "/",
            "\\",
            "|",
            "`",
            "~",
        ]

        for char in invalid_chars:
            with self.assertRaises(ValidationError):
                validate_storage_name(f"test-name{char}123.test")

    def test_validate_uniqueness_storage_name_for_storage_type(self):
        name_to_validate = "unique_name_01"
        another_unique_name = "unique_name_02"

        storage_2_name_to_validate = Storage2Factory()
        create_allocation_attribute(
            storage_2_name_to_validate,
            "storage_name",
            name_to_validate,
        )

        storage_2_name_to_validate_deleted = Storage2Factory(
            status__name="Deleted",
        )
        create_allocation_attribute(
            storage_2_name_to_validate_deleted,
            "storage_name",
            name_to_validate,
        )

        # This should raise an error because an active allocation with this name and type exists
        with self.assertRaises(ValidationError):
            validate_uniqueness_storage_name_for_storage_type(
                name_to_validate,
                "Storage2",
            )

        # This should not raise an error because the existing allocation with this name is deleted
        validate_uniqueness_storage_name_for_storage_type(
            another_unique_name,
            "Storage2",
        )

        # This should not raise an error because the existing allocation with this name is of a different storage type
        validate_uniqueness_storage_name_for_storage_type(
            name_to_validate,
            "Storage3",
        )
        # This should not raise an error because both the name and storage type are different
        validate_uniqueness_storage_name_for_storage_type(
            another_unique_name,
            "Storage3",
        )
