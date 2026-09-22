import os
from typing import Any, Optional, Union
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv

load_dotenv(override=True)


class WorkdayApiError(Exception):
    def __init__(self, message, status=None, body=None):
        super().__init__(message)
        self.status = status
        self.body = body


# Workday's Learning module is used to track access attestations, via
# indexedLearningAssignmentRecords -- there is no dedicated "attestation"
# business object. cf_ZCF_EE_UniversalID is aliased "universal_id"
# deliberately, not "wustlkey" -- the underlying value is AD's wustlEduId,
# NOT a real wustlkey (AD's sAMAccountName). See
# ActiveDirectoryAPI.find_wustlkey_by_universal_id, which resolves the two.
#
# This query has no dedicated attestation-cycle field. learningContent2 (the
# specific attestation/training content's WID, pinned to one value in the
# WHERE clause below) is used as the closest available "which cycle"
# identifier; confirm with the Workday team whether a better field exists.
OVERDUE_ATTESTATIONS_WQL = (
    "SELECT learningParticipant, learningContent2, required1, assignmentStatus1, "
    "assignmentMechanism1, dueDate1, "
    "cf_ZCF_EE_OverdueConsidersIfLearningEnrollmentsAreComplete as Overdue, "
    "cf_ZCF_EE_UniversalID as universal_id, "
    "worker1{employeeID, cf_ZCF_EEB_WorkerStatusEvaluated_Updated, email_PrimaryWork, "
    "manager_Level01, cf_ZCF_LRV_Level1ManagerEmail, jobTitle} as Worker "
    "FROM indexedLearningAssignmentRecords "
    "WHERE learningContent2 in (a5c5126c1b5a10020807b9a582640000) "
    "AND cf_ZCF_EE_OverdueConsidersIfLearningEnrollmentsAreComplete = 'Yes' "
    "AND assignmentMechanism1 in ('1880266fd7ec10001501ed8dffd81498') "
    "ORDER BY dueDate1 ASC"
)


class WorkdayAPI:
    """Queries Workday for overdue access attestations, used to gate storage
    allocation access provisioning (see utils/attestation.py). Mirrors
    ../../../ris-user-management-tmp/python/clients/workday_client.py's
    OVERDUE_ATTESTATIONS_WQL/get_overdue_attestations so the two independent
    callers agree on what "overdue" means, without sharing code or a process.
    """

    def __init__(self) -> None:
        self.url = os.environ.get("WORKDAY_URL")
        self.tenant = os.environ.get("WORKDAY_TENANT", "wustl6")
        self.client_id = os.environ.get("WORKDAY_OAUTH_CLIENT_ID")
        self.client_secret = os.environ.get("WORKDAY_OAUTH_CLIENT_SECRET")
        self.refresh_token = os.environ.get("WORKDAY_OAUTH_REFRESH_TOKEN")
        self._cached_token: Optional[str] = None

    def _token_url(self) -> str:
        return f"{self.url.rstrip('/')}/ccx/oauth2/{self.tenant}/token"

    def _wql_url(self, wql: str) -> str:
        endpoint = f"{self.url.rstrip('/')}/api/wql/v1/{self.tenant}/data"
        return f"{endpoint}?{urlencode({'query': wql})}"

    def _get_verify_certificate(self) -> Union[str, bool]:
        # Matches ItsmClientHandler's convention: this can be a path to a
        # certificate bundle, or True to use the default trust store.
        return os.environ.get("RIS_CHAIN_CERTIFICATE") or True

    def _get_access_token(self) -> str:
        # Imported lazily: shared_lib is IntegrationHub-managed infrastructure,
        # not a pip dependency of this project, so this module (and everything
        # that imports it) still imports and can be unit tested on a machine
        # that doesn't have it on the path. It's only required at the moment a
        # real Workday call is made.
        from shared_lib.auth.oauth2 import get_workday_token

        if self._cached_token is None:
            self._cached_token = get_workday_token(
                self.client_id, self.client_secret, self._token_url(), self.refresh_token
            )
            if not self._cached_token:
                raise WorkdayApiError("Failed to obtain Workday access token from refresh token")
        return self._cached_token

    def run_wql(self, wql: str) -> Any:
        url = self._wql_url(wql)
        headers = {"Accept": "application/json", "Authorization": f"Bearer {self._get_access_token()}"}
        try:
            response = requests.get(url, headers=headers, timeout=30, verify=self._get_verify_certificate())
        except requests.RequestException as error:
            raise WorkdayApiError(f"Workday WQL request failed: {error}") from error

        if not response.ok:
            raise WorkdayApiError(
                f"Workday WQL request failed: {response.status_code}: {response.text[:500]}",
                response.status_code,
                response.text,
            )

        try:
            return response.json()
        except ValueError as error:
            raise WorkdayApiError(
                f"Workday WQL request failed: response wasn't valid JSON "
                f"(status {response.status_code}): {response.text[:500]!r}",
                response.status_code,
            ) from error

    def get_overdue_attestations(self) -> list[dict[str, Any]]:
        """Returns [{"universal_id", "attestation_cycle_id", "due_date"}, ...]
        for every user whose access attestation is currently overdue.

        universal_id is Workday's cf_ZCF_EE_UniversalID (an integer), i.e.
        AD's wustlEduId -- not a wustlkey. Callers must resolve it to a
        wustlkey via ActiveDirectoryAPI.find_wustlkey_by_universal_id before
        using it against ColdFront/AD. attestation_cycle_id is populated
        from learningContent2 (see the caveat on OVERDUE_ATTESTATIONS_WQL
        above).
        """
        data = self.run_wql(OVERDUE_ATTESTATIONS_WQL)
        rows = data.get("data", []) if isinstance(data, dict) else []
        overdue = []
        for row in rows:
            universal_id = row.get("universal_id")
            if universal_id is None:
                continue
            overdue.append(
                {
                    "universal_id": universal_id,
                    "attestation_cycle_id": row.get("learningContent2"),
                    "due_date": row.get("dueDate1"),
                }
            )
        return overdue
