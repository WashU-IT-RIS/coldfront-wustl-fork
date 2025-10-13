import requests
import ldap3
from qumulo.rest_client import RestClient

import os, json

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        qumulo_info = json.loads(os.environ.get("QUMULO_INFO"))

        for qumulo_host in qumulo_info:
            storage_host = qumulo_host["host"]
            request_res = requests.get(
                "https://" + storage_host + "/api/v1/version", verify=False
            )
            print(f"Pod connects to Storage: {request_res.status_code == 200}")
            print(request_res.json())

            rc = RestClient(storage_host, qumulo_host["port"])
            rc.login(qumulo_host["user"], qumulo_host["pass"])

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

        print(f"Pod connects to AD: {conn.bind()}")

        try:
            rc.ad.list_ad()
            print(f"Storage connects to AD")
        except Exception as e:
            print(f"Storage doesn't connect to Storage")
