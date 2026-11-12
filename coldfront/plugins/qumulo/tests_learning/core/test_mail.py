from unittest import skip
from django.test import TestCase, tag
from formencode.validators import Email
from coldfront.core.test_helpers.factories import (
    AllocationFactory,
    AllocationUserFactory,
    ProjectUserFactory,
    ProjectUserStatusChoiceFactory,
)
from coldfront.core.utils.mail import allocation_email_recipients
from coldfront.plugins.qumulo.tests.fixtures import create_metadata_for_testing


class TestLearningMail(TestCase):

    def setUp(self) -> None:
        create_metadata_for_testing()
        return super().setUp()

    @tag("learning")
    @tag("skip")
    def test_allocation_email_recipients(self):
        allocation = AllocationFactory()
        project_user = ProjectUserFactory(
            user=allocation.project.pi,
            project=allocation.project,
            status__name="Active",
        )
        allocation_user = AllocationUserFactory(
            user=project_user.user, allocation=allocation
        )

        recipients = allocation_email_recipients(allocation_user.allocation)
        self.assertIsInstance(recipients, list)
        self.assertTrue(all(Email.to_python(email) for email in recipients))
        self.assertIn(allocation_user.allocation.project.pi.email, recipients)
        self.assertIn(allocation_user.user.email, recipients)
