import os

STORAGE_ROOT = os.environ.get("STORAGE2_PATH").strip("/")

def fileset_name_to_storage_filesystem_path(fileset_name):
    # In ITSM, fileset_names are mapped into name
    # Examples
    # bisiademuyiwa_active --> /storage2/fs1/bisiademuyiwa
    # gc6159 --> /storage2/fs1/gc6159
    fileset_name_seed = fileset_name.split("_active")[0]
    storage_filesystem_path = f"/{STORAGE_ROOT}/{fileset_name_seed}" 

    return storage_filesystem_path

def fileset_name_to_storage_export_path(fileset_name):
    # TODO I cannot figure out from the code how to populate this.
    fileset_name_seed = fileset_name.split("_active")[0]
    export_path = f"/{STORAGE_ROOT}/{fileset_name_seed}" 

    return export_path

def comment_to_protocols(value:dict):
    return ["smb"]
"""
    # I was under the impression that nfs was the default; however,
    # after inspecting the migrated allocations, all of them have ["smb"] as the protocol.
    protocols = ["nfs"] # Add nfs always according to business rule

    if value.get("smb_export_name"):
        protocols.append("smb")
    return protocols
"""

def fileset_name_to_storage_name(value):
    # Examples: fileset_name= "jiaoy_active" --> "jiaoy"
    # fileset_name= "gc6159" --> "gc6159"
    return value.split("_active")[0]

def acl_group_members_to_aggregate_create_users(value):
    # Example: "akronzer,derek.harford,d.ken,ehogue,jiaoy,perezm,xuebing".split(",")
    # return ['akronzer', 'derek.harford', 'd.ken', 'ehogue', 'jiaoy', 'perezm', 'xuebing']
    # from this array, create a user from every element in the array
    return value.split(",")
