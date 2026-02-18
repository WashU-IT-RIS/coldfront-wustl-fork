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
