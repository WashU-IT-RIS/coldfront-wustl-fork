from django.core.management.base import BaseCommand

from django.contrib.auth.models import Group, Permission

DEFAULT_RIS_USERSUPPORT_GROUP_PERMISSIONS = [
    {"id": 167, "codename": "add_allocation"},
    {"id": 168, "codename": "change_allocation"},
    {"id": 169, "codename": "delete_allocation"},
    {"id": 170, "codename": "view_allocation"},
    {"id": 171, "codename": "can_view_all_allocations"},
    {"id": 172, "codename": "can_review_allocation_requests"},
    {"id": 173, "codename": "can_manage_invoice"},
    {"id": 174, "codename": "add_allocationattribute"},
    {"id": 175, "codename": "change_allocationattribute"},
    {"id": 176, "codename": "delete_allocationattribute"},
    {"id": 177, "codename": "view_allocationattribute"},
    {"id": 178, "codename": "add_allocationattributetype"},
    {"id": 179, "codename": "change_allocationattributetype"},
    {"id": 180, "codename": "delete_allocationattributetype"},
    {"id": 181, "codename": "view_allocationattributetype"},
    {"id": 182, "codename": "add_allocationstatuschoice"},
    {"id": 183, "codename": "change_allocationstatuschoice"},
    {"id": 184, "codename": "delete_allocationstatuschoice"},
    {"id": 185, "codename": "view_allocationstatuschoice"},
    {"id": 186, "codename": "add_allocationuserstatuschoice"},
    {"id": 187, "codename": "change_allocationuserstatuschoice"},
    {"id": 188, "codename": "delete_allocationuserstatuschoice"},
    {"id": 189, "codename": "view_allocationuserstatuschoice"},
    {"id": 190, "codename": "add_attributetype"},
    {"id": 191, "codename": "change_attributetype"},
    {"id": 192, "codename": "delete_attributetype"},
    {"id": 193, "codename": "view_attributetype"},
    {"id": 194, "codename": "add_allocationattributeusage"},
    {"id": 195, "codename": "change_allocationattributeusage"},
    {"id": 196, "codename": "delete_allocationattributeusage"},
    {"id": 197, "codename": "view_allocationattributeusage"},
    {"id": 198, "codename": "add_historicalallocationuser"},
    {"id": 199, "codename": "change_historicalallocationuser"},
    {"id": 200, "codename": "delete_historicalallocationuser"},
    {"id": 201, "codename": "view_historicalallocationuser"},
    {"id": 202, "codename": "add_historicalallocationattributeusage"},
    {"id": 203, "codename": "change_historicalallocationattributeusage"},
    {"id": 204, "codename": "delete_historicalallocationattributeusage"},
    {"id": 205, "codename": "view_historicalallocationattributeusage"},
    {"id": 206, "codename": "add_historicalallocationattributetype"},
    {"id": 207, "codename": "change_historicalallocationattributetype"},
    {"id": 208, "codename": "delete_historicalallocationattributetype"},
    {"id": 209, "codename": "view_historicalallocationattributetype"},
    {"id": 210, "codename": "add_historicalallocationattribute"},
    {"id": 211, "codename": "change_historicalallocationattribute"},
    {"id": 212, "codename": "delete_historicalallocationattribute"},
    {"id": 213, "codename": "view_historicalallocationattribute"},
    {"id": 214, "codename": "add_historicalallocation"},
    {"id": 215, "codename": "change_historicalallocation"},
    {"id": 216, "codename": "delete_historicalallocation"},
    {"id": 217, "codename": "view_historicalallocation"},
    {"id": 218, "codename": "add_allocationusernote"},
    {"id": 219, "codename": "change_allocationusernote"},
    {"id": 220, "codename": "delete_allocationusernote"},
    {"id": 221, "codename": "view_allocationusernote"},
    {"id": 222, "codename": "add_allocationuser"},
    {"id": 223, "codename": "change_allocationuser"},
    {"id": 224, "codename": "delete_allocationuser"},
    {"id": 225, "codename": "view_allocationuser"},
    {"id": 226, "codename": "add_allocationadminnote"},
    {"id": 227, "codename": "change_allocationadminnote"},
    {"id": 228, "codename": "delete_allocationadminnote"},
    {"id": 229, "codename": "view_allocationadminnote"},
    {"id": 230, "codename": "add_allocationaccount"},
    {"id": 231, "codename": "change_allocationaccount"},
    {"id": 232, "codename": "delete_allocationaccount"},
    {"id": 233, "codename": "view_allocationaccount"},
    {"id": 234, "codename": "add_allocationchangerequest"},
    {"id": 235, "codename": "change_allocationchangerequest"},
    {"id": 236, "codename": "delete_allocationchangerequest"},
    {"id": 237, "codename": "view_allocationchangerequest"},
    {"id": 238, "codename": "add_allocationchangestatuschoice"},
    {"id": 239, "codename": "change_allocationchangestatuschoice"},
    {"id": 240, "codename": "delete_allocationchangestatuschoice"},
    {"id": 241, "codename": "view_allocationchangestatuschoice"},
    {"id": 242, "codename": "add_historicalallocationchangerequest"},
    {"id": 243, "codename": "change_historicalallocationchangerequest"},
    {"id": 244, "codename": "delete_historicalallocationchangerequest"},
    {"id": 245, "codename": "view_historicalallocationchangerequest"},
    {"id": 246, "codename": "add_historicalallocationattributechangerequest"},
    {"id": 247, "codename": "change_historicalallocationattributechangerequest"},
    {"id": 248, "codename": "delete_historicalallocationattributechangerequest"},
    {"id": 249, "codename": "view_historicalallocationattributechangerequest"},
    {"id": 250, "codename": "add_allocationattributechangerequest"},
    {"id": 251, "codename": "change_allocationattributechangerequest"},
    {"id": 252, "codename": "delete_allocationattributechangerequest"},
    {"id": 253, "codename": "view_allocationattributechangerequest"},
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
            print(f"Creating group: {group['name']}")
            Group.objects.get_or_create(name=group["name"])
            for permission in group["permissions"]:
                print(f"Adding permission: {permission['codename']}")
                group_obj = Group.objects.get(name=group["name"])
                group_obj.permissions.add(Permission.objects.get(id=permission["id"]))

        print("Finished creating default user groups")
