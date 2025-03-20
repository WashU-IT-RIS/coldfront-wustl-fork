from unittest import skip
from django.test import TestCase, tag
from coldfront.core.test_helpers.factories import AllocationFactory
from coldfront.core.utils.mail import allocation_email_recipients
from coldfront.plugins.qumulo.tests.fixtures import create_metadata_for_testing

class TestLearningMail(TestCase):

    def setUp(self) -> None:
        create_metadata_for_testing()
        return super().setUp()

    @skip("in progress")
    @tag("learning")
    def test_allocation_email_recipients(self):
        allocation = AllocationFactory()
        recipient = allocation_email_recipients(allocation)
        self.assertContains()
