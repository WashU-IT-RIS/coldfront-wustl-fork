from coldfront.plugins.qumulo.services.itsm.migrate_to_coldfront import (
    MigrateToColdfront,
)


storage3_path = "/storage3/fs1"

# washu_keys must be passed as arguments

class_members_washu_keys = [f"class_member_washu_key{i}" for i in range(5)]
acl_permissions = {"ro": "class_permissions_ro", "rw": "class_permissions_rw"}
dir_projects = {washu_key: acl_permissions for washu_key in class_members_washu_keys}

# adjust data below accordingly
allocation_attributes_class_ris = [
    {
        "id": 10000,
        "service_id": 1,
        "name": "/vol/rdcw-fs1/course",
        "sponsor": "course_ris",
        "department_number": "CH00409",
        "department_name": "Genetics",
        "funding_number": "CC0004259",
        "billing_contact": "course_ris",
        "technical_contact": "course_ris",
        "secure": False,
        "service_desk_ticket_number": "ITSD-2222",
        "audit": None,
        "creation_timestamp": "2020-04-16T00: 00: 00.000Z",
        "billing_startdate": "2020-04-15T00: 00: 00.000Z",
        "status": "active",
        "sponsor_department_number": "CH00409",
        "fileset_name": "course_ris_active",
        "fileset_alias": "course_ris_active",
        "exempt": False,
        "service_rate_category": "consumption",
        "comment": dir_projects,
        "billing_cycle": "monthly",
        "subsidized": True,
        "quota": "200T",
        "allow_nonfaculty": None,
        "acl_group_members": "fup,course_ris",
        "who": "rpokorne",
        "parent_id": None,
        "is_condo_group": False,
        "sla": None,
        "_service_provision": 10000,
        "_department": "CH00409",
    }
]

migrator = MigrateToColdfront()
# migrator.set_override("storage_quota", "2")
# if the quota is set above, the override is not necessary.
# "quota": "0.5T",
migrator.batch_create_allocations_and_sub_allocations(
    "class_ris", "storage3", allocation_attributes_class_ris
)
