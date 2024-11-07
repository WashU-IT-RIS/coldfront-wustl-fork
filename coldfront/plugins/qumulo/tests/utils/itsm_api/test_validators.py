from django.test import TestCase, Client

from unittest.mock import patch, MagicMock

from coldfront.plugins.qumulo.services.itsm.fields.validators import (
    numericallity,
    presence_of,
    length_of,
    inclusion_of,
    validate_ticket,
)


class TestValidators(TestCase):

    def setUp(self) -> None:
        return super().setUp()

    def test_validate_ticket(self):
        self.assertTrue(validate_ticket("ITSD-2222"))
        self.assertTrue(validate_ticket("itsd-2222"))
        self.assertTrue(validate_ticket("2222"))
        self.assertTrue(validate_ticket(2222))

        exception_message = (
            'Service desk ticket "ITSD" must have format: ITSD-12345 or 12345'
        )
        self.assertRaises(Exception, validate_ticket, "ITSD", msg=exception_message)
        self.assertRaises(
            Exception, validate_ticket, "ITDEV-2222", msg=exception_message
        )
        self.assertRaises(
            Exception, validate_ticket, "itsd2222", msg=exception_message
        )

    def test_numericallity(self) -> None:
        conditions = {
            "only_integer": True,
            "greater_than": 0,
            "less_than_or_equal_to": 2000,
        }
        # Truthy conditions
        self.assertTrue(numericallity(200, conditions))
        self.assertTrue(numericallity(1, conditions))
        self.assertTrue(numericallity(2000, conditions))
        # Falsy conditions
        self.assertFalse(numericallity(-1, conditions))
        self.assertFalse(numericallity(1.2, conditions))
        self.assertFalse(numericallity(None, conditions))
        self.assertFalse(numericallity(0, conditions))

    def test_presence_of(self):
        presence = True
        # Truthy when presense is required
        value = "something"
        self.assertTrue(presence_of(value, presence))
        value = 10
        self.assertTrue(presence_of(value, presence))
        value = ["monthly"]
        self.assertTrue(presence_of(value, presence))

        # Falsy when presense is required
        value = ""
        self.assertFalse(presence_of(value, presence))
        value = None
        self.assertFalse(presence_of(value, presence))

        # when presence is not required (optional)
        value = ""
        self.assertTrue(presence_of(value, False))
        value = None
        self.assertTrue(presence_of(value, False))

    def test_length_of(self):
        conditions = {"allow_blank": True, "maximum": 128}
        # value = ""
        # self.assertTrue(length_of(value, conditions))
        # value = None
        # self.assertTrue(length_of(value, conditions))

        conditions = {"maximum": 128}
        value = ""
        self.assertFalse(length_of(value, conditions))
        value = None
        self.assertFalse(length_of(value, conditions))

    def test_inclusion_of(self):
        accpeted_values = ["monthly", "yearly", "quarterly", "prepaid", "fiscal year"]
        self.assertTrue(inclusion_of("quarterly", accpeted_values))
        self.assertFalse(inclusion_of(None, accpeted_values))
        self.assertFalse(inclusion_of(True, accpeted_values))
        self.assertFalse(inclusion_of(1, accpeted_values))
        self.assertFalse(inclusion_of("Rube Goldberg", accpeted_values))

        accpeted_values = [True, False, "0", "1", None]
        self.assertTrue(inclusion_of("0", accpeted_values))
        self.assertTrue(inclusion_of("1", accpeted_values))
        self.assertTrue(inclusion_of(0, accpeted_values))
        self.assertTrue(inclusion_of(1, accpeted_values))
        self.assertTrue(inclusion_of(False, accpeted_values))
        self.assertTrue(inclusion_of(True, accpeted_values))
        self.assertTrue(inclusion_of(None, accpeted_values))

        self.assertFalse(inclusion_of(2, accpeted_values))
        self.assertFalse(inclusion_of("2", accpeted_values))


"""
from coldfront.plugins.qumulo.services.itsm.validators.allocation_attributes import numericallity
coldfront/plugins/qumulo/tests/utils.itsm_api.test_validators
"""
