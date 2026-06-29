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

    def get_group_members(self, group_name: str) -> str:
        self.conn.search(
            "dc=accounts,dc=ad,dc=wustl,dc=edu",
            f"(&(objectClass=group)(sAMAccountName={group_name}))",
            # attributes = ['member']
            attributes=ALL_ATTRIBUTES
        )

        if not self.conn.response:
            raise ValueError("Invalid group name")

        return self.conn.response[0]

    def get_user_by_dn(self, dn: str):
        if not dn:
            raise ValueError("dn must be defined")

        try:
            self.conn.search(
                "dc=accounts,dc=ad,dc=wustl,dc=edu",
                f"(&(objectClass=person)(distinguishedName={dn}))",
                attributes=ALL_ATTRIBUTES,
            )
        except ldap3.core.exceptions.LDAPInvalidFilterError:
            print(f'DEBUG: invalid filter for: {dn}', flush=True)

        if not self.conn.response:
            raise ValueError("Invalid user dn")

        return self.conn.response[0]

    def get_group_by_dn(self, dn: str):
        if not dn:
            raise ValueError("dn must be defined")

        self.conn.search(
            "dc=accounts,dc=ad,dc=wustl,dc=edu",
            f"(&(objectClass=group)(distinguishedName={dn}))",
            attributes=ALL_ATTRIBUTES,
        )

        if not self.conn.response:
            raise ValueError("Invalid group dn")

        return self.conn.response[0]

    def _process_group_members(self, members):
        group_members = set()
        if type(members) == type(list()):
            for member_dn in members:
                if not member_dn:
                    continue
                member_data = None
                try:
                    member_data = self.get_user_by_dn(member_dn)
                except ValueError:
                    pass
                if member_data is None:
                    continue
                member_wustlkey = member_data.get('attributes', {}) \
                                    .get('sAMAccountName')
                if member_wustlkey:
                    resolved_member = self.resolve_id(member_wustlkey)
                    if resolved_member['id_is_user']:
                        group_members.add(member_wustlkey)
                    elif resolved_member['id_is_group']:
                        group_members.update(
                            self._process_group_members(
                                list(resolved_member['data'])
                            )
                        )
        return group_members

    def resolve_id(self, identifier):
        return_dict = {
            'id_is_user': True,
            'id_is_group': True,
            'data': None
        }
        try:
            self.get_user(identifier)
        except ValueError:
            return_dict['id_is_user'] = False
        if return_dict['id_is_user']:
            # identifier refers to a user
            return_dict['id_is_group'] = False
            return return_dict
        try:
            member_response = self.get_group_members(identifier)
        except ValueError:
            return_dict['id_is_group'] = False
        if not return_dict['id_is_group']:
            # identifier (somehow) refers to neither a user nor a group
            return return_dict
        # identifier refers to a group; build a list of IDs if "member" is a list
        return_dict['data'] = self._process_group_members(
            member_response.get('attributes', {}).get('member', [])
        )
        print(f'processing group {identifier}; user list is {return_dict["data"]}', flush=True)
        subgroup_dns = member_response.get('attributes', {}) \
                        .get('managedObjects', [])
        if type(subgroup_dns) == type(list()):
            for subgroup_dn in subgroup_dns:
                try:
                    subgroup_data = self.get_group_by_dn(subgroup_dn)
                except ValueError:
                    pass
                subgroup_cn = subgroup_data.get('attributes', {}).get('cn')
                if subgroup_cn:
                    resolved_subgroup = self.resolve_id(subgroup_cn)
                    if resolved_subgroup['data'] is not None:
                        return_dict['data'].update(resolved_subgroup['data'])
        return return_dict
