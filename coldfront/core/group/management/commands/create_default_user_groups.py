from django.core.management.base import BaseCommand

from django.contrib.auth.models import Group, Permission

DEFAULT_RIS_USERSUPPORT_GROUP_PERMISSIONS = [
    {"codename": "add_allocation"},
    {"codename": "change_allocation"},
    {"codename": "delete_allocation"},
    {"codename": "view_allocation"},
    {"codename": "can_view_all_allocations"},
    {"codename": "can_review_allocation_requests"},
    {"codename": "can_manage_invoice"},
    {"codename": "add_allocationattribute"},
    {"codename": "change_allocationattribute"},
    {"codename": "delete_allocationattribute"},
    {"codename": "view_allocationattribute"},
    {"codename": "add_allocationattributetype"},
    {"codename": "change_allocationattributetype"},
    {"codename": "delete_allocationattributetype"},
    {"codename": "view_allocationattributetype"},
    {"codename": "add_allocationstatuschoice"},
    {"codename": "change_allocationstatuschoice"},
    {"codename": "delete_allocationstatuschoice"},
    {"codename": "view_allocationstatuschoice"},
    {"codename": "add_allocationuserstatuschoice"},
    {"codename": "change_allocationuserstatuschoice"},
    {"codename": "delete_allocationuserstatuschoice"},
    {"codename": "view_allocationuserstatuschoice"},
    {"codename": "add_attributetype"},
    {"codename": "change_attributetype"},
    {"codename": "delete_attributetype"},
    {"codename": "view_attributetype"},
    {"codename": "add_allocationattributeusage"},
    {"codename": "change_allocationattributeusage"},
    {"codename": "delete_allocationattributeusage"},
    {"codename": "view_allocationattributeusage"},
    {"codename": "add_historicalallocationuser"},
    {"codename": "change_historicalallocationuser"},
    {"codename": "delete_historicalallocationuser"},
    {"codename": "view_historicalallocationuser"},
    {"codename": "add_historicalallocationattributeusage"},
    {"codename": "change_historicalallocationattributeusage"},
    {"codename": "delete_historicalallocationattributeusage"},
    {"codename": "view_historicalallocationattributeusage"},
    {"codename": "add_historicalallocationattributetype"},
    {"codename": "change_historicalallocationattributetype"},
    {"codename": "delete_historicalallocationattributetype"},
    {"codename": "view_historicalallocationattributetype"},
    {"codename": "add_historicalallocationattribute"},
    {"codename": "change_historicalallocationattribute"},
    {"codename": "delete_historicalallocationattribute"},
    {"codename": "view_historicalallocationattribute"},
    {"codename": "add_historicalallocation"},
    {"codename": "change_historicalallocation"},
    {"codename": "delete_historicalallocation"},
    {"codename": "view_historicalallocation"},
    {"codename": "add_allocationusernote"},
    {"codename": "change_allocationusernote"},
    {"codename": "delete_allocationusernote"},
    {"codename": "view_allocationusernote"},
    {"codename": "add_allocationuser"},
    {"codename": "change_allocationuser"},
    {"codename": "delete_allocationuser"},
    {"codename": "view_allocationuser"},
    {"codename": "add_allocationadminnote"},
    {"codename": "change_allocationadminnote"},
    {"codename": "delete_allocationadminnote"},
    {"codename": "view_allocationadminnote"},
    {"codename": "add_allocationaccount"},
    {"codename": "change_allocationaccount"},
    {"codename": "delete_allocationaccount"},
    {"codename": "view_allocationaccount"},
    {"codename": "add_allocationchangerequest"},
    {"codename": "change_allocationchangerequest"},
    {"codename": "delete_allocationchangerequest"},
    {"codename": "view_allocationchangerequest"},
    {"codename": "add_allocationchangestatuschoice"},
    {"codename": "change_allocationchangestatuschoice"},
    {"codename": "delete_allocationchangestatuschoice"},
    {"codename": "view_allocationchangestatuschoice"},
    {"codename": "add_historicalallocationchangerequest"},
    {"codename": "change_historicalallocationchangerequest"},
    {"codename": "delete_historicalallocationchangerequest"},
    {"codename": "view_historicalallocationchangerequest"},
    {"codename": "add_historicalallocationattributechangerequest"},
    {"codename": "change_historicalallocationattributechangerequest"},
    {"codename": "delete_historicalallocationattributechangerequest"},
    {"codename": "view_historicalallocationattributechangerequest"},
    {"codename": "add_allocationattributechangerequest"},
    {"codename": "change_allocationattributechangerequest"},
    {"codename": "delete_allocationattributechangerequest"},
    {"codename": "view_allocationattributechangerequest"},
]
DEFAULT_RIS_USER_GROUPS = [
    {
        "name": "RIS-UserSupport",
        "permissions": DEFAULT_RIS_USERSUPPORT_GROUP_PERMISSIONS,
    }
]


class Command(BaseCommand):
    """
    Command to create default user groups.
    """

    help = "Create default user groups"

    def handle(self, *args, **options):
        print("Creating default user groups ...")
        for group in DEFAULT_RIS_USER_GROUPS:
            Group.objects.get_or_create(name=group["name"])
            for permission in group["permissions"]:
                group_obj = Group.objects.get(name=group["name"])
                group_obj.permissions.add(
                    Permission.objects.get(codename=permission["codename"])
                )

        print("Finished creating default user groups")
