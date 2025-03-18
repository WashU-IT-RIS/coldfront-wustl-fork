from django.test import TestCase
from coldfront.core.test_helpers.factories import AllocationFactory
from coldfront.core.utils.mail import allocation_email_recipients

class TestLearningMail(TestCase):

    def setUp(self) -> None:
        return super().setUp()

    def test_allocation_email_recipients(self):
        allocation = AllocationFactory()
        recipient = allocation_email_recipients(allocation)
        self.assertContains()