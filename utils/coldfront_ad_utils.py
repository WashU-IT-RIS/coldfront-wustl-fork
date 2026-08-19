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
            attributes=["wustlEduHRPrimeDeptName","wustlEduOLSDisplayName"]
            # attributes=ALL_ATTRIBUTES,
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
            attributes=ALL_ATTRIBUTES,
            # attributes=["sAMAccountName", "mail", "givenName", "sn"],
            # attributes=["sAMAccountName"],
        )

        if not self.conn.response:
            raise ValueError("Invalid department")

        return self.conn.response

    def get_group_members(self, group_name):
        if not group_name:
            raise ValueError(("department must be defined"))

        self.conn.search(
            "dc=accounts,dc=ad,dc=wustl,dc=edu",
            f"(&(objectClass=group)(samAccountName={group_name}))",
            attributes=['member'],
        )

        if not self.conn.response:
            raise ValueError("Invalid department")

        return self.conn.response

