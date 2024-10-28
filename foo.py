mock_quotas = {
    "quotas": [
        {
            "id": "111111111",
            "path": "/storage2/fs1/not_found_in_coldfront/",
            "limit": "20000000000000",
            "capacity_usage": "1",
        },
        {
            "id": "18600003",
            "path": "/storage2/fs1/sleong/",
            "limit": "100000000000000",
            "capacity_usage": "37089736126464",
        },
        {
            "id": "34717218",
            "path": "/storage2/fs1/prewitt_test/",
            "limit": "1099511627776",
            "capacity_usage": "53248",
        },
        {
            "id": "36270003",
            "path": "/storage2/fs1/tychele_test/",
            "limit": "109951162777600",
            "capacity_usage": "57344",
        },
        {
            "id": "36290003",
            "path": "/storage2/fs1/tychele_test/Active/tychele_suballoc_test/",
            "limit": "109951162777600",
            "capacity_usage": "4096",
        },
        {
            "id": "36850003",
            "path": "/storage2/fs1/prewitt_test/Active/prewitt_test_2_a/",
            "limit": "1099511627776",
            "capacity_usage": "4096",
        },
        {
            "id": "36860003",
            "path": "/storage2/fs1/prewitt_test_2/",
            "limit": "1099511627776",
            "capacity_usage": "16384",
        },
        {
            "id": "37000005",
            "path": "/storage2/fs1/jian_test/",
            "limit": "10995116277760",
            "capacity_usage": "16384",
        },
        {
            "id": "38760894",
            "path": "/storage2/fs1/hong.chen_test/",
            "limit": "5497558138880",
            "capacity_usage": "40960",
        },
        {
            "id": "38760895",
            "path": "/storage2/fs1/i2_test/",
            "limit": "109951162777600",
            "capacity_usage": "20480",
        },
        {
            "id": "39720243",
            "path": "/storage2/fs1/swamidass_test/",
            "limit": "24189255811072",
            "capacity_usage": "16384",
        },
        {
            "id": "39720382",
            "path": "/storage2/fs1/prewitt_test_3/",
            "limit": "5497558138880",
            "capacity_usage": "16384",
        },
        {
            "id": "42020003",
            "path": "/storage2/fs1/hong.chen_test/Active/hong.chen_suballocation/",
            "limit": "5497558138880",
            "capacity_usage": "4096",
        },
        {
            "id": "42030003",
            "path": "/storage2/fs1/engineering_test/",
            "limit": "5497558138880",
            "capacity_usage": "307242479616",
        },
        {
            "id": "42030004",
            "path": "/storage2/fs1/sleong_summer/",
            "limit": "5497558138880",
            "capacity_usage": "713363001344",
        },
        {
            "id": "42050003",
            "path": "/storage2/fs1/wexler_test/",
            "limit": "5497558138880",
            "capacity_usage": "16384",
        },
        {
            "id": "42080003",
            "path": "/storage2/fs1/alex.holehouse_test/",
            "limit": "38482906972160",
            "capacity_usage": "16384",
        },
        {
            "id": "42080004",
            "path": "/storage2/fs1/wucci/",
            "limit": "5497558138880",
            "capacity_usage": "16384",
        },
        {
            "id": "42130003",
            "path": "/storage2/fs1/amlai/",
            "limit": "5497558138880",
            "capacity_usage": "4198400",
        },
        {
            "id": "43010004",
            "path": "/storage2/fs1/jin810_test/",
            "limit": "109951162777600",
            "capacity_usage": "16384",
        },
        {
            "id": "43010005",
            "path": "/storage2/fs1/dinglab_test/",
            "limit": "109951162777600",
            "capacity_usage": "16384",
        },
        {
            "id": "43050003",
            "path": "/storage2/fs1/wucci_test/",
            "limit": "109951162777600",
            "capacity_usage": "16384",
        },
        {
            "id": "43070003",
            "path": "/storage2/fs1/gtac-mgi_test2/",
            "limit": "5497558138880",
            "capacity_usage": "1477898227712",
        },
        {
            "id": "52929566",
            "path": "/storage2/fs1/mweil_test/",
            "limit": "5497558138880",
            "capacity_usage": "1436366471168",
        },
        {
            "id": "52929567",
            "path": "/storage2/fs1/amlai_test2/",
            "limit": "16492674416640",
            "capacity_usage": "997732352",
        },
        {
            "id": "52929568",
            "path": "/storage2/fs1/tychele_test2/",
            "limit": "109951162777600",
            "capacity_usage": "18083368955904",
        },
    ],
    "paging": {"next": ""},
}

quota_mock_allocation_data = {
    "/storage2/fs1/sleong/": {"limit": "100000000000000"},
    "/storage2/fs1/prewitt_test/": {"limit": "1099511627776"},
    "/storage2/fs1/tychele_test": {"limit": "109951162777600"},
    "/storage2/fs1/tychele_test/Active/tychele_suballoc_test": {
        "limit": "109951162777600"
    },
    "/storage2/fs1/prewitt_test/Active/prewitt_test_2_a": {"limit": "1099511627776"},
    "/storage2/fs1/prewitt_test_2": {"limit": "1099511627776"},
    "/storage2/fs1/jian_test": {"limit": "10995116277760"},
    "/storage2/fs1/hong.chen_test": {"limit": "5497558138880"},
    "/storage2/fs1/i2_test": {"limit": "109951162777600"},
    "/storage2/fs1/swamidass_test": {"limit": "24189255811072"},
    "/storage2/fs1/prewitt_test_3": {"limit": "5497558138880"},
    "/storage2/fs1/hong.chen_test/Active/hong.chen_suballocation": {
        "limit": "5497558138880"
    },
    "/storage2/fs1/engineering_test": {"limit": "5497558138880"},
    "/storage2/fs1/sleong_summer": {"limit": "5497558138880"},
    "/storage2/fs1/wexler_test": {"limit": "5497558138880"},
    "/storage2/fs1/alex.holehouse_test": {"limit": "38482906972160"},
    "/storage2/fs1/wucci": {"limit": "5497558138880"},
    "/storage2/fs1/amlai": {"limit": "5497558138880"},
    "/storage2/fs1/jin810_test": {"limit": "109951162777600"},
    "/storage2/fs1/dinglab_test": {"limit": "109951162777600"},
    "/storage2/fs1/wucci_test": {"limit": "109951162777600"},
    "/storage2/fs1/gtac-mgi_test2": {"limit": "5497558138880"},
    "/storage2/fs1/mweil_test": {"limit": "5497558138880"},
    "/storage2/fs1/amlai_test2": {"limit": "16492674416640"},
    "/storage2/fs1/tychele_test2": {"limit": "109951162777600"},
}

import json

# print(len(mock_quotas["quotas"]))
# print(len(quota_mock_allocation_data.keys()))

new_dict = {}
for key, value in quota_mock_allocation_data.items():
    new_value = {}
    new_value["limit"] = value["limit"]

    quota = next(
        filter(
            lambda quota: quota["path"].strip("/") == key.strip("/"),
            mock_quotas["quotas"],
        )
    )
    new_value["id"] = quota["id"]
    new_value["usage"] = quota["capacity_usage"]

    new_key = "/" + key.strip("/") + "/"
    new_dict[new_key] = new_value

print(json.dumps(new_dict, indent=4, sort_keys=True))
