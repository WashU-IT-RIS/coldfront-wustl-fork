import os
from typing import Any, Optional
import requests


class ItsmClientHandler:
    def __init__(self):
        self.user = os.environ.get("ITSM_SERVICE_USER")
        self.password = os.environ.get("ITSM_SERVICE_PASSWORD")
        self.host = os.environ.get("ITSM_HOST")
        protocol = os.environ.get("ITSM_PROTOCOL")
        port = os.environ.get("ITSM_REST_API_PORT")
        endpoint_path = os.environ.get("ITSM_SERVICE_PROVISION_ENDPOINT")
        self.url = f"{protocol}://{self.host}:{port}{endpoint_path}"

    def get_data(self, attributes: str, filters: str) -> str:
        session = self._get_session()
        filtered_url = self._get_filtered_url(attributes, filters)
        response = session.get(filtered_url, verify=self._get_verify_certificate())
        response.raise_for_status()

        data = response.json().get("data")
        session.close()
        return data

    # Private methods

    def _is_itsm_localhost(self):
        return self.host == "localhost"

    def _get_session(self) -> requests.Session:
        session = requests.Session()
        session.auth = self._get_session_authentication()
        session.headers = self._get_session_headers()
        return session

    def _get_session_headers(self) -> dict:
        headers = {"content-type": "application/json"}
        if self._is_itsm_localhost():
            headers["x-remote-user"] = self.user

        return headers

    def _get_session_authentication(self) -> Optional[tuple]:
        if self._is_itsm_localhost():
            return None

        return (self.user, self.password)

    def _get_verify_certificate(self) -> Any:
        # Unfortunately, the verify attribute could be a path where the certificate is located or bool
        return os.environ.get("RIS_CHAIN_CERTIFICATE") or True

    def _get_filtered_url(self, attributes: str, filters: str) -> str:
        return f"{self.url}?filter={filters}&attribute={attributes}"
