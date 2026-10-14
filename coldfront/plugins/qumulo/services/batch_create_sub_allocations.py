from coldfront.plugins.qumulo.services.itsm.migrate_to_coldfront import (
    MigrateToColdfront,
)


storage3_path = "/storage3/fs1"

class_members_washu_keys = [f"class_member_washu_key{i}" for i in range(5)]
acl_permissions = {"ro": "class_permissions_ro", "rw": "class_permissions_rw"}
dir_projects = {washu_key: acl_permissions for washu_key in class_members_washu_keys}

allocation_attributes_class_ris = [
    {
        "id": 774,
        "service_id": 1,
        "name": "/vol/rdcw-fs1/jin810",
        "sponsor": "jin810",
        "department_number": "CH00409",
        "department_name": "Genetics",
        "funding_number": "CC0004259",
        "billing_contact": "jin810",
        "technical_contact": "jin810",
        "secure": False,
        "service_desk_ticket_number": "ITSD-2222",
        "audit": None,
        "creation_timestamp": "2020-04-16T00: 00: 00.000Z",
        "billing_startdate": "2020-04-15T00: 00: 00.000Z",
        "status": "active",
        "sponsor_department_number": "CH00409",
        "fileset_name": "jin810_active",
        "fileset_alias": "jin810_active",
        "exempt": False,
        "service_rate_category": "subscription",
        "comment": '{"dir_projects":{"KHADER":{"ro":null,"rw":null},"KHADER_ADMIN":{"ro":null,"rw":["mushtaqahmed","pamelacamp"]},"KHADERLAB_PROTOCOLS":{"ro":["akter","bobba.suhas","chauhank","darya.urusova","lmellett","lulan","ncaleb","rswanson","s.thirunavukkarasu","sbmehta","yangyan"],"rw":["g.ananya","mushtaqahmed","shibalidas"]},"KHADERLAB_TBPROGRAM":{"ro":null,"rw":["akter","bobba.suhas","chauhank","darya.urusova","g.ananya","lmellett","lulan","mushtaqahmed","ncaleb","pamelacamp","rswanson","s.thirunavukkarasu","sbmehta","shibalidas","yangyan"]},"PAPER_2018":{"ro":null,"rw":["shibalidas"]},"Khader_lab":{"ro":null,"rw":["jmartin"]},"Khadercompute":{"ro":null,"rw":["akter","bobba.suhas","jmartin","mushtaqahmed","sakhader"]},"Shared_With_Max":{"ro":null,"rw":["akter","mushtaqahmed","shibalidas","storage-martyomov"]},"MGI_Data":{"rw":["barosa","jmartin","storage-sakhader-khaderlab_tbprogram-rw"],"ro":[]},"MGI_Data":{"rw":["barosa","jmartin","storage-sakhader-khaderlab_tbprogram-rw"],"ro":[]},"archive_test_data":{"rw":["barosa","jmartin"],"ro":[],"archive":true}}}',
        "billing_cycle": "monthly",
        "subsidized": True,
        "quota": "200T",
        "allow_nonfaculty": None,
        "acl_group_members": "fup,jin810",
        "who": "rpokorne",
        "parent_id": None,
        "is_condo_group": False,
        "sla": None,
        "_service_provision": 774,
        "_department": "CH00409",
    }
]

migrator = MigrateToColdfront()
migrator.set_override("storage_quota", "2")
migrator.batch_create_sub_allocations(
    "class_ris", "storage3", allocation_attributes_class_ris
)
