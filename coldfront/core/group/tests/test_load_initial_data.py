from django.core.management import call_command
from django.test import TestCase
from django.core.management.base import CommandError
from unittest.mock import patch
from coldfront.core.group.migrations.load_initial_data import load_initial_data


class LoadInitialDataTest(TestCase):
    @patch("django.core.management.call_command")
    def test_load_initial_data_success(self, mock_call_command):
        """Test that load_initial_data calls loaddata with correct fixture"""
        load_initial_data(None, None)
        mock_call_command.assert_called_once_with("loaddata", "default_user_groups")

    @patch("django.core.management.call_command")
    def test_load_initial_data_failure(self, mock_call_command):
        """Test that load_initial_data handles CommandError"""
        mock_call_command.side_effect = CommandError("Error loading data")
        with self.assertRaises(CommandError):
            load_initial_data(None, None)
