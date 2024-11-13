import os
import requests

from dotenv import load_dotenv

from coldfront.plugins.qumulo.services.itsm.fields.itsm_to_coldfront_factory import (
    itsm_attributes,
)

load_dotenv(override=True)


class ItsmClient:
    def __init__(self):
        self.user = os.environ.get("ITSM_USER")
        self.password = os.environ.get("ITSM_PASSWORD")  # get it from secrets
        protocol = os.environ.get("ITSM_PROTOCOL")
        host = os.environ.get("ITSM_HOST")
        port = os.environ.get("ITSM_PORT")
        endpoint_path = os.environ.get("ITSM_SERVICE_PROVISION_ENDPOINT")

        # TODO is there a way to get the name of the environment such as prod, qa, or localhost?
        self.is_itsm_localhost = host == "localhost"

        itsm_fields = ",".join(itsm_attributes)
        self.url = f"{protocol}://{host}:{port}{endpoint_path}?attribute={itsm_fields}"

    def get_fs1_allocation_by_fileset_name(self, fileset_name) -> str:
        return self.__get_fs1_allocation_by("fileset_name", fileset_name)

    def get_fs1_allocation_by_fileset_alias(self, fileset_alias) -> str:
        return self.__get_fs1_allocation_by("fileset_alias", fileset_alias)

    #### PRIVATE METHODS ####
    def __get_fs1_allocation_by(self, fileset_key, fileset_value) -> str:
        filtered_url = self.__get_filtered_url(fileset_key, fileset_value)
        session = requests.Session()
        self.__set_session_authentication(session)
        self.__set_session_headers(session)
        response = session.get(filtered_url)
        response.raise_for_status()

        data = response.json().get("data")
        session.close()
        return data

    def __get_filtered_url(self, fileset_key, fileset_value) -> str:
        filters = f'filter={{"{fileset_key}":"{fileset_value}"}}'
        return f"{self.url}&{filters}"

    def __set_session_headers(self, session) -> None:
        headers = {"content-type": "application/json"}
        if self.is_itsm_localhost:
            headers["x-remote-user"] = self.user

        session.headers = headers
        return

    def __set_session_authentication(self, session) -> None:
        if self.is_itsm_localhost:
            return

        session.auth = (self.user, self.password)
        return


""" 
# For manual testing

from coldfront.plugins.qumulo.services.itsm.itsm_client import ItsmClient

itsm_client = ItsmClient()
itsm_client.get_fs1_allocation_by_fileset_name("jin810_active")
itsm_client.get_fs1_allocation_by_fileset_name("not_going_to_be_found") # returns []
itsm_client.get_fs1_allocation_by_fileset_name(None) # returns []
itsm_client.get_fs1_allocation_by_fileset_name() # TypeError: get_fs1_allocation_by_fileset_name() missing 1 required positional argument: 'fileset_name'
itsm_client.get_fs1_allocation_by_fileset_alias("halllab")
itsm_client.get_fs1_allocation_by_fileset_alias("not_going_to_be_found") # returns []
itsm_client.get_fs1_allocation_by_fileset_alias(None) # returns []
itsm_client.get_fs1_allocation_by_fileset_alias() # TypeError: get_fs1_allocation_by_fileset_alias() missing 1 required positional argument: 'fileset_alias'
"""
