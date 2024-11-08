from django.test import TestCase, Client

from unittest.mock import patch, MagicMock

from coldfront.plugins.qumulo.services.itsm.fields.validators import (
    numericallity,
    presence,
    length,
    inclusion,
    validate_ticket,
    validate_json
)

class TestValidators(TestCase):

    def setUp(self) -> None:
        return super().setUp()

    def test_validate_json(self):
        wellformed = """
        {"afm_cache_enable":true,"dir_projects":{"brc_regulome":{"ro":null,"rw":["mgi-svc-bga-admin","mgi-svc-bga-run"]},"bga1641":{"ro":null,"rw":["mgi-svc-bga-admin","mgi-svc-bga-run","jwalker"]}},"_jenkins":"https://systems-ci.gsc.wustl.edu/job/storage1_allocation/2483"}
        """
        self.assertTrue(validate_json(wellformed))

        empty = "{}"
        self.assertTrue(validate_json(empty))

        malformed = """
        {"afm_cache_enable":bad}
        """
        self.assertFalse(validate_json(malformed))

        conditions = {"allow_blank": True}
        blank = ""
        self.assertTrue(validate_json(blank, conditions))
        self.assertTrue(validate_json(None, conditions))


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
        self.assertRaises(Exception, validate_ticket, "itsd2222", msg=exception_message)

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

    def test_presence(self):
        # Truthy when presense is required
        value = "something"
        self.assertTrue(presence(value, True))
        value = 10
        self.assertTrue(presence(value, True))
        value = ["monthly"]
        self.assertTrue(presence(value, True))

        # Falsy when presense is required
        value = ""
        self.assertFalse(presence(value, True))
        value = None
        self.assertFalse(presence(value, True))

        # when presence is not required (optional)
        value = ""
        self.assertTrue(presence(value, False))
        value = None
        self.assertTrue(presence(value, False))

    def test_length(self):
        conditions = {"allow_blank": True, "maximum": 128}
        value = ""
        self.assertTrue(length(value, conditions))
        value = None
        self.assertTrue(length(value, conditions))
        value = "0123456789" * 12 # 120 chars
        self.assertTrue(length(value, conditions))
        value = "0123456789" * 13 # 130 chars
        self.assertFalse(length(value, conditions))

        conditions = {"maximum": 128}
        value = ""
        self.assertFalse(length(value, conditions))
        value = None
        self.assertFalse(length(value, conditions))
        value = "0123456789" * 12
        self.assertTrue(length(value, conditions))
        value = "0123456789" * 13
        self.assertFalse(length(value, conditions))

    def test_inclusion(self):
        accpeted_values = ["monthly", "yearly", "quarterly", "prepaid", "fiscal year"]
        self.assertTrue(inclusion("quarterly", accpeted_values))
        self.assertFalse(inclusion(None, accpeted_values))
        self.assertFalse(inclusion(True, accpeted_values))
        self.assertFalse(inclusion(1, accpeted_values))
        self.assertFalse(inclusion("Rube Goldberg", accpeted_values))

        accpeted_values = [True, False, "0", "1", None]
        self.assertTrue(inclusion("0", accpeted_values))
        self.assertTrue(inclusion("1", accpeted_values))
        self.assertTrue(inclusion(0, accpeted_values))
        self.assertTrue(inclusion(1, accpeted_values))
        self.assertTrue(inclusion(False, accpeted_values))
        self.assertTrue(inclusion(True, accpeted_values))
        self.assertTrue(inclusion(None, accpeted_values))

        self.assertFalse(inclusion(2, accpeted_values))
        self.assertFalse(inclusion("2", accpeted_values))

def test_ad_record_exist(value):
    #TODO how?
    pass


"""
from coldfront.plugins.qumulo.services.itsm.fields.validators import numericallity
coldfront/plugins/qumulo/tests/utils.itsm_api.test_validators
"""
