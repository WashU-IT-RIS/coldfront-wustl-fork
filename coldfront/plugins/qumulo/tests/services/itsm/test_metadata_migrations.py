import json
from django.test import TestCase

from unittest import mock
from unittest.mock import patch

from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttribute,
)
from coldfront.core.project.models import Project, ProjectAttribute

from coldfront.plugins.qumulo.services.itsm.migrate_to_coldfront import (
    MigrateToColdfront,
)
from coldfront.plugins.qumulo.tests.fixtures import create_metadata_for_testing
from coldfront.plugins.qumulo.tests.utils.mock_data import mock_qumulo_info

class TestMetadataMigrations(TestCase):
    def setUp(self):
        # Create a mock allocation and project for testing
        self.allocation = Allocation.objects.create(name="Test Allocation")
        self.project = Project.objects.create(name="Test Project", allocation=self.allocation)

        # Add mock metadata attributes to the project
        create_metadata_for_testing(self.project)

        # Initialize the migration service
        self.migration_service = MigrateToColdfront(self.project)

    @patch('coldfront.plugins.qumulo.services.itsm.migrate_to_coldfront.get_user_by_email')
    def test_migrate_metadata(self, mock_get_user_by_email):
        # Mock user lookup responses
        ...

# sponsor has an email
# if found, should convert email to whashu_key
# if not found, should reject migration
# if multiple found, reject migration with an exception

# billing_contact has an email
# if found, should convert email to whashu_key
# if not found, should set to None and notify through a warning message

# technical_contact has an email
# if found, should convert email to whashu_key
# if not found, should set to None and notify through a warning message

# create sub allocations from the project_dir in itsm comment fields
# if project_dir exists, should create sub allocations
# if not, should skip since the allocation has no sub allocations

# create users from the rw and ro in the itsm comment fields
# if user exists, should create user
# if not, should skip and notify through a warning message

