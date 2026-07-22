from coldfront.plugins.qumulo.utils.active_directory_api import ActiveDirectoryAPI
from ldap3 import ALL_ATTRIBUTES

import ldap3
import os
from dotenv import load_dotenv

load_dotenv(override=True)

# class ResolvedIdentifier:
#     is_user = True
#     is_group = True
#     data = None
#     return_dict = {
#         'id_is_user': True,
#         'id_is_group': True,
#         'data': None
#     }
# 
#     def group(self):
#         self.is_group = False


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

    def get_department_users(self, department: str):
        if not department:
            raise ValueError(("department must be defined"))

        self.conn.search(
            "dc=accounts,dc=ad,dc=wustl,dc=edu",
            f"(&(objectClass=person)(wustlEduHRPrimeDeptName={department}))",
            # attributes=["sAMAccountName", "mail", "givenName", "sn"],
            attributes=ALL_ATTRIBUTES,
            # attributes=["wustlEduHRPrimeDeptName","wustlEduOLSDisplayName"]
            # attributes=["sAMAccountName"],
        )

        if not self.conn.response:
            raise ValueError("Invalid department")

        return self.conn.response
