import sys
import types
from unittest.mock import MagicMock, patch

from django.test import TestCase

from coldfront.plugins.qumulo.utils.workday_api import WorkdayApiError, WorkdayAPI


os_environ = {
    "WORKDAY_URL": "https://workday.example.com",
    "WORKDAY_TENANT": "wustl6",
    "WORKDAY_OAUTH_CLIENT_ID": "client-id",
    "WORKDAY_OAUTH_CLIENT_SECRET": "client-secret",
    "WORKDAY_OAUTH_REFRESH_TOKEN": "refresh-token",
}


def _fake_shared_lib(get_workday_token=None):
    """Injects a fake shared_lib.auth.oauth2 module into sys.modules so
    WorkdayAPI._get_access_token's lazy `from shared_lib.auth.oauth2 import
    get_workday_token` succeeds without the real (IntegrationHub-managed,
    non-pip) package installed.
    """
    oauth2_module = types.ModuleType("shared_lib.auth.oauth2")
    oauth2_module.get_workday_token = get_workday_token or MagicMock(return_value="fake-token")
    auth_module = types.ModuleType("shared_lib.auth")
    auth_module.oauth2 = oauth2_module
    shared_lib_module = types.ModuleType("shared_lib")
    shared_lib_module.auth = auth_module
    return {
        "shared_lib": shared_lib_module,
        "shared_lib.auth": auth_module,
        "shared_lib.auth.oauth2": oauth2_module,
    }


class TestWorkdayAPI(TestCase):
    def setUp(self):
        patch.dict("os.environ", os_environ).start()
        self.workday_api = WorkdayAPI()

    def tearDown(self):
        patch.stopall()
        return super().tearDown()

    def test_token_url_and_wql_url(self):
        self.assertEqual(
            self.workday_api._token_url(), "https://workday.example.com/ccx/oauth2/wustl6/token"
        )
        self.assertIn(
            "https://workday.example.com/api/wql/v1/wustl6/data?query=",
            self.workday_api._wql_url("SELECT foo"),
        )

    def test_get_access_token_fetches_via_shared_lib_and_caches(self):
        get_workday_token = MagicMock(return_value="fake-token")
        with patch.dict(sys.modules, _fake_shared_lib(get_workday_token)):
            token = self.workday_api._get_access_token()
            token_again = self.workday_api._get_access_token()

        get_workday_token.assert_called_once_with(
            "client-id", "client-secret", "https://workday.example.com/ccx/oauth2/wustl6/token", "refresh-token"
        )
        self.assertEqual(token, "fake-token")
        self.assertEqual(token_again, "fake-token")

    def test_get_access_token_raises_when_no_token_returned(self):
        with patch.dict(sys.modules, _fake_shared_lib(MagicMock(return_value=None))):
            with self.assertRaises(WorkdayApiError):
                self.workday_api._get_access_token()

    @patch("coldfront.plugins.qumulo.utils.workday_api.requests.get")
    def test_run_wql_returns_parsed_json_on_success(self, mock_get):
        mock_get.return_value = MagicMock(ok=True, json=lambda: {"data": [{"foo": "bar"}]})

        with patch.object(WorkdayAPI, "_get_access_token", return_value="fake-token"):
            result = self.workday_api.run_wql("SELECT foo")

        self.assertEqual(result, {"data": [{"foo": "bar"}]})
        called_headers = mock_get.call_args.kwargs["headers"]
        self.assertEqual(called_headers["Authorization"], "Bearer fake-token")

    @patch("coldfront.plugins.qumulo.utils.workday_api.requests.get")
    def test_run_wql_raises_clear_error_on_non_ok_response(self, mock_get):
        mock_get.return_value = MagicMock(ok=False, status_code=500, text="server error")

        with patch.object(WorkdayAPI, "_get_access_token", return_value="fake-token"):
            with self.assertRaises(WorkdayApiError):
                self.workday_api.run_wql("SELECT foo")

    @patch("coldfront.plugins.qumulo.utils.workday_api.requests.get")
    def test_run_wql_raises_clear_error_on_non_json_response(self, mock_get):
        def raise_value_error():
            raise ValueError("not json")

        mock_get.return_value = MagicMock(ok=True, json=raise_value_error, text="<html>oops</html>")

        with patch.object(WorkdayAPI, "_get_access_token", return_value="fake-token"):
            with self.assertRaises(WorkdayApiError):
                self.workday_api.run_wql("SELECT foo")

    def test_get_overdue_attestations_parses_rows_and_skips_missing_universal_id(self):
        rows = [
            {"universal_id": 12345, "learningContent2": "att_2026_q3", "dueDate1": "2026-09-01"},
            {"learningContent2": "att_2026_q3", "dueDate1": "2026-09-02"},
        ]
        with patch.object(self.workday_api, "run_wql", return_value={"data": rows}):
            overdue = self.workday_api.get_overdue_attestations()

        self.assertEqual(
            overdue,
            [{"universal_id": 12345, "attestation_cycle_id": "att_2026_q3", "due_date": "2026-09-01"}],
        )

    def test_get_overdue_attestations_handles_empty_response(self):
        with patch.object(self.workday_api, "run_wql", return_value={}):
            self.assertEqual(self.workday_api.get_overdue_attestations(), [])
