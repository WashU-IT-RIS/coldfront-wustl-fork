from pprint import pprint

from coldfront.core.allocation.models import (
    Allocation,
    AllocationUser,
    AllocationAttribute,
)
from coldfront.plugins.qumulo.utils.active_directory_api import ActiveDirectoryAPI


def align_ad_groups():
    storage_allocation_pks = Allocation.objects.active_storage().values_list(
        "pk", flat=True
    )

    storage_allocation_pks = list(map(lambda x: str(x), storage_allocation_pks))

    acl_allocation_pks = (
        AllocationAttribute.objects.filter(
            allocation_attribute_type__name="storage_allocation_pk"
        )
        .filter(
            value__in=storage_allocation_pks,
        )
        .values_list("allocation", flat=True)
    )

    acl_allocations = Allocation.objects.filter(pk__in=acl_allocation_pks)

    ad_api = ActiveDirectoryAPI()

    misalignments = []
    for allocation in acl_allocations:
        additional_errors = []
        group_name = allocation.get_attribute("storage_acl_name")
        allocation_users = AllocationUser.objects.filter(allocation=allocation)
        allocation_usernames = [
            allocation_user.user.username for allocation_user in allocation_users
        ]

        try:
            ad_members = ad_api.get_group_members(group_name)
        except ValueError:
            # Group missing in AD or has no members
            additional_errors.append(f"Group {group_name} missing in AD.")
            ad_members = []
        except Exception as e:
            print(f"Error fetching AD members for group {group_name}: {e}")
            exit(1)

        allocation_set = {name.lower() for name in allocation_usernames}
        ad_set = {name.lower() for name in ad_members if name}

        only_in_allocation = sorted(allocation_set - ad_set)
        only_in_allocation = ad_api.get_members(only_in_allocation)
        only_in_allocation = [
            member["attributes"]["sAMAccountName"] for member in only_in_allocation
        ]

        only_in_ad = sorted(ad_set - allocation_set)

        if only_in_allocation or only_in_ad or additional_errors:
            misalignments.append(
                {
                    "allocation_pk": allocation.pk,
                    "group_name": group_name,
                    "in_allocation_not_in_ad": only_in_allocation,
                    "in_ad_not_in_allocation": only_in_ad,
                    "additional_errors": additional_errors,
                }
            )

    pprint(misalignments)
