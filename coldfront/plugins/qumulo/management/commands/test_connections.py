import requests
import ldap3
from qumulo.rest_client import RestClient

import os
from dotenv import load_dotenv

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        storage_host = os.environ.get("QUMULO_HOST")
        request_res = requests.get("https://" + storage_host + "/api/v1/version")
        print(f"Connects to Storage: {request_res.status_code == 200}")
        print(request_res.json())

        rc = RestClient(storage_host, os.environ.get("QUMULO_PORT"))
        rc.login(os.environ.get("QUMULO_USER"), os.environ.get("QUMULO_PASS"))

        try:
            rc.ad.list_ad()
            print(f"Storage Connects to Qumulo: {request_res.status_code == 200}")
        except Exception as e:
            print(f"Doesn't connect to Storage: ${e}")

        serverName = os.environ.get("AD_SERVER_NAME")
        adUser = os.environ.get("AD_USERNAME")
        adUserPwd = os.environ.get("AD_USER_PASS")

        server = ldap3.Server(host=serverName, use_ssl=True, get_info=ldap3.ALL)
        conn = ldap3.Connection(
            server,
            user="ACCOUNTS\\" + adUser,
            password=adUserPwd,
            authentication=ldap3.NTLM,
        )

        print(f"connects to AD: ${conn.bind()}")
