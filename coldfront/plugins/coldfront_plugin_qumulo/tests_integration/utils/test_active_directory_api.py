from django.test import TestCase
from coldfront_plugin_qumulo.utils.active_directory_api import ActiveDirectoryAPI


class TestActiveDirectoryAPI(TestCase):
    def setUp(self) -> None:
        self.ad_api = ActiveDirectoryAPI()
        self.test_wustlkey = "harterj"
        self.user_in_group_filter = (
            lambda group_name: f"(&(objectClass=user)(sAMAccountName={self.test_wustlkey})(memberof=CN={group_name},OU=QA,OU=RIS,OU=Groups,DC=accounts,DC=ad,DC=wustl,DC=edu))"
        )

        return super().setUp()

    def tearDown(self) -> None:
        self.ad_api.conn.search(
            "dc=accounts,dc=ad,dc=wustl,dc=edu", "(cn=storage-delme-test*)"
        )

        test_groups = self.ad_api.conn.response
        for group in test_groups:
            self.ad_api.conn.delete(group["dn"])

    def test_init_creates_connection(self):
        self.assertTrue(self.ad_api.conn.bind())

    def test_get_user(self):
        user = self.ad_api.get_user(self.test_wustlkey)

        self.assertIn("Harter", user["dn"])

    def test_create_ad_group(self):
        group_name = "storage-delme-test-create_ad_group"

        self.ad_api.create_ad_group(group_name=group_name)

        group_dn = self.ad_api.get_group_dn(group_name)
        self.assertGreater(len(group_dn), 0)

    def test_add_user_to_ad_group(self):
        group_name = "storage-delme-test-add_user_to_ad_group"

        self.ad_api.create_ad_group(group_name=group_name)
        self.ad_api.add_user_to_ad_group(
            wustlkey=self.test_wustlkey, group_name=group_name
        )

        search_filter = self.user_in_group_filter(group_name)

        user_in_group = self.ad_api.conn.search(
            search_base="dc=accounts,dc=ad,dc=wustl,dc=edu",
            search_filter=search_filter,
        )

        self.assertTrue(user_in_group)

    def test_get_group_dn(self):
        group_name = "storage-delme-test-get_group_dn"

        self.ad_api.create_ad_group(group_name=group_name)

        self.ad_api.conn.search(
            "dc=accounts,dc=ad,dc=wustl,dc=edu",
            f"(cn={group_name})",
        )
        group_dn = self.ad_api.conn.response[0]["dn"]
        response_group_dn = self.ad_api.get_group_dn(group_name)

        self.assertEqual(response_group_dn, group_dn)

    def test_delete_ad_group(self):
        group_name = "storage-delme-test-delete_ad_group"

        self.ad_api.create_ad_group(group_name=group_name)
        self.ad_api.conn.search(
            "dc=accounts,dc=ad,dc=wustl,dc=edu",
            f"(cn={group_name})",
        )
        self.assertEqual(len(self.ad_api.conn.response), 1)

        self.ad_api.delete_ad_group(group_name)

        self.ad_api.conn.search(
            "dc=accounts,dc=ad,dc=wustl,dc=edu",
            f"(cn={group_name})",
        )
        self.assertEqual(len(self.ad_api.conn.response), 0)

    def test_remove_user_from_group(self):
        group_name = "storage-delme-test-remove_user_from_group"

        self.ad_api.create_ad_group(group_name=group_name)
        self.ad_api.add_user_to_ad_group(
            wustlkey=self.test_wustlkey, group_name=group_name
        )

        user_in_group = self.ad_api.conn.search(
            search_base="dc=accounts,dc=ad,dc=wustl,dc=edu",
            search_filter=self.user_in_group_filter(group_name),
        )
        self.assertTrue(user_in_group)

        self.ad_api.remove_user_from_group(self.test_wustlkey, group_name)
        user_in_group = self.ad_api.conn.search(
            search_base="dc=accounts,dc=ad,dc=wustl,dc=edu",
            search_filter=self.user_in_group_filter(group_name),
        )

        self.assertFalse(user_in_group)
