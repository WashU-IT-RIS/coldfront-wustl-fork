from coldfront.plugins.qumulo.utils.active_directory_api import ActiveDirectoryAPI
from ldap3 import ALL_ATTRIBUTES

import os
from dotenv import load_dotenv

load_dotenv(override=True)

class ColdfrontAdUtils(ActiveDirectoryAPI):

    def get_user_department(self, wustlkey: str):
        if not wustlkey:
            raise ValueError(("wustlkey must be defined"))

        self.conn.search(
            "dc=accounts,dc=ad,dc=wustl,dc=edu",
            f"(&(objectClass=person)(sAMAccountName={wustlkey}))",
            # attributes=["sAMAccountName", "mail", "givenName", "sn"],
            attributes=ALL_ATTRIBUTES,
            # attributes=["wustlEduHRPrimeDeptName","wustlEduOLSDisplayName"]
        )

        if not self.conn.response:
            raise ValueError("Invalid wustlkey")

        return self.conn.response[0]

