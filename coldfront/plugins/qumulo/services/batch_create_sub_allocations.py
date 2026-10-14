import csv
import json

from coldfront.plugins.qumulo.services.itsm.migrate_to_coldfront import (
    MigrateToColdfront,
)


storage3_path = "/storage3/fs1"

# class_members_washu_keys_csv = globals().get(
#     "class_washu_keys", "class_members_washu_keys.csv"
# )
# with open(class_members_washu_keys_csv, newline="", encoding="utf-8") as keys_file:
#     class_members_washu_keys = [
#         row[0].strip()
#         for row in csv.reader(keys_file)
#         if row
#         and row[0].strip()
#         and row[0].strip().lower()
#         not in {"washu_key", "class_member_washu_key"}
#     ]

# acl_permissions = {"ro": ["class_permissions_ro"], "rw": ["class_permissions_rw"]}
# dir_projects = {washu_key: acl_permissions for washu_key in class_members_washu_keys}

allocation_attributes_json = globals().get("allocation_attributes")
if allocation_attributes_json is None:
    allocation_attributes_json = "allocation_attributes_class_ris.json"
with open(allocation_attributes_json, encoding="utf-8") as allocation_file:
    allocation_attributes_class_ris = json.load(allocation_file)

if not isinstance(allocation_attributes_class_ris, list) or not all(
    isinstance(attributes, dict) for attributes in allocation_attributes_class_ris
):
    raise ValueError("Allocation attributes JSON must contain a list of objects.")


migrator = MigrateToColdfront()
migrator.batch_create_allocations_and_sub_allocations(
    "di2-cap", "Storage3", allocation_attributes_class_ris
)
