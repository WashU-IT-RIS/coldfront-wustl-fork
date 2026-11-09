from pprint import pprint

from coldfront.core.allocation.models import Allocation, AllocationUser
from coldfront.plugins.qumulo.utils.active_directory_api import ActiveDirectoryAPI


def align_ad_groups():
    acl_allocations = Allocation.objects.filter(resources__resource_type__name="ACL")
    ad_api = ActiveDirectoryAPI()

    for allocation in acl_allocations:
        group_name = allocation.get_attribute("storage_acl_name")
        allocation_users = AllocationUser.objects.filter(allocation=allocation)
        allocation_usernames = [
            allocation_user.user.username for allocation_user in allocation_users
        ]

        try:
            ad_members = ad_api.get_group_members(group_name)
        except ValueError:
            # Group missing in AD or has no members
            ad_members = []

        allocation_set = {name.lower() for name in allocation_usernames}
        ad_set = {name.lower() for name in ad_members if name}

        only_in_allocation = sorted(allocation_set - ad_set)
        only_in_ad = sorted(ad_set - allocation_set)

        if only_in_allocation or only_in_ad:
            print(f"Misalignment for allocation {allocation.pk} / group {group_name}")
            pprint(
                {
                    "in_allocation_not_in_ad": only_in_allocation,
                    "in_ad_not_in_allocation": only_in_ad,
                }
            )
