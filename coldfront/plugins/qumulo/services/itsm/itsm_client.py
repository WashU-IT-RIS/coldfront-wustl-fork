import os
import requests

from dotenv import load_dotenv

from coldfront.plugins.qumulo.services.itsm.fields.allocation_fields_factory import (
    itsm_attributes,
)

load_dotenv(override=True)

class ItsmClient:
    def __init__(self):
        self.user = os.environ.get("ITSM_USER") or "sleong"
        protocol = os.environ.get("ITSM_PROTOCOL") or "http"
        host = os.environ.get("ITSM_HOST") or "localhost"
        port = os.environ.get("ITSM_PORT") or "3000"

        itsm_fields = ",".join(itsm_attributes)
        self.url = f"{protocol}://{host}:{port}/rest/attr/info/service_provision?attribute={itsm_fields}"

    def get_fs1_allocation(self, fileset_name) -> str:
        filtered_url = self.__get_filtered_url(fileset_name)
        response = requests.get(filtered_url, headers=self.__get_headers())
        response.raise_for_status()

        data = response.json().get("data")
        return data

    def __get_filtered_url(self, fileset_name) -> str:
        filters = f'filter={{"fileset_alias":"{fileset_name}"}}'
        return f"{self.url}&{filters}"

    def __get_headers(self) -> dict:
        return {"content-type": "application/json", "x-remote-user": self.user}


""" 
For manual testing
from coldfront.plugins.qumulo.services.itsm.itsm_client import ItsmClient
itsm_client = ItsmClient()
itsm_client.get_fs1_allocation("jin810_active")
itsm_client.get_fs1_allocation("not_going_to_be_found")
itsm_client.get_fs1_allocation() 
"""

"""
# TODO Delete

fileset_name = "jin810_active"
import os
import requests
from dotenv import load_dotenv
from coldfront.plugins.qumulo.services.itsm.allocation_fields_factory import (
    itsm_attributes,
)
protocol = os.environ.get("ITSM_PROTOCOL") or "http"
host = os.environ.get("ITSM_HOST") or "localhost"
port = os.environ.get("ITSM_PORT") or "3000"
user = os.environ.get("ITSM_USER") or "sleong"
itsm_fields = ",".join(itsm_attributes)
url = f"{protocol}://{host}:{port}/rest/attr/info/service_provision?attribute={itsm_fields}"
headers = {"x-remote-user": user, "content-type": "application/json"}
filters = f'filter={{"fileset_alias":"{fileset_name}"}}'
filtered_url = f"{url}&{filters}"
response = requests.get(filtered_url, headers=headers)
"""
