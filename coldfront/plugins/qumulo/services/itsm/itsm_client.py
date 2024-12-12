import os
import requests

from dotenv import load_dotenv

from coldfront.plugins.qumulo.services.itsm.fields.itsm_to_coldfront_fields_factory import (
    itsm_attributes,
)

load_dotenv(override=True)


class ItsmClient:
    def __init__(self):
        self.user = os.environ.get("ITSM_SERVICE_USER")
        self.password = os.environ.get("ITSM_SERVICE_PASSWORD")
        protocol = os.environ.get("ITSM_PROTOCOL")
        host = os.environ.get("ITSM_HOST")
        port = os.environ.get("ITSM_REST_API_PORT")
        endpoint_path = os.environ.get("ITSM_SERVICE_PROVISION_ENDPOINT")

        itsm_fields = ",".join(itsm_attributes)
        self.url = f"{protocol}://{host}:{port}{endpoint_path}?attribute={itsm_fields}"

    def get_fs1_allocation_by_fileset_name(self, fileset_name) -> str:
        return self.__get_fs1_allocation_by("fileset_name", fileset_name)

    def get_fs1_allocation_by_fileset_alias(self, fileset_alias) -> str:
        return self.__get_fs1_allocation_by("fileset_alias", fileset_alias)

    # TODO is there a way to get the name of the environment such as prod, qa, or localhost?
    def is_itsm_localhost(self, host):
        return host == "localhost"

    #### PRIVATE METHODS ####
    def __get_fs1_allocation_by(self, fileset_key, fileset_value) -> str:
        filtered_url = self.__get_filtered_url(fileset_key, fileset_value)
        session = self.__get_session()
        response = session.get(filtered_url, verify=self.__get_verify_certificate())
        response.raise_for_status()

        data = response.json().get("data")
        session.close()
        return data

    def __get_filtered_url(self, fileset_key, fileset_value) -> str:
        itsm_active_allocation_service_id = 1
        filters = f'filter={{"{fileset_key}":"{fileset_value}","status":"active","service_id":{itsm_active_allocation_service_id}}}'
        return f"{self.url}&{filters}"

    def __get_session(self):
        session = requests.Session()
        session.auth = self.__get_session_authentication()
        session.headers = self.__get_session_headers()
        return session

    def __get_session_headers(self) -> None:
        headers = {"content-type": "application/json"}
        if self.is_itsm_localhost:
            headers["x-remote-user"] = self.user

        return headers

    def __get_session_authentication(self) -> None:
        if self.is_itsm_localhost:
            return

        return (self.user, self.password)

    def __get_verify_certificate(self):
        return os.environ.get("RIS_CHAIN_CERTIFICATE") or True
