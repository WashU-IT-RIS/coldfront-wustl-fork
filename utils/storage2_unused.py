from coldfront.core.allocation.models import Allocation, AllocationAttribute
from coldfront.core.billing.models import AllocationUsage

def get_attributes(allocation_id):
    return_dict = {'storage_groups': []}
    # main allocation attributes
    for attribute in (
        AllocationAttribute
            .objects
            .filter(allocation_id=allocation_id)
    ):
        return_dict[str(attribute)] = attribute.value
    for attribute in (
        AllocationAttribute
            .objects
            .filter(value=allocation_id)
    ):
        if str(attribute) != 'storage_allocation_pk':
            continue
        for storage_attribute in (
            AllocationAttribute
                .objects
                .filter(allocation_id=attribute.allocation_id)
        ):
            if str(storage_attribute) != 'storage_acl_name':
                continue
            return_dict['storage_groups'].append(storage_attribute.value)
    if len(return_dict['storage_groups']) == 0:
        return_dict['storage_groups'].append("N/A")
    return return_dict

storage_names = set()
print(
    (
        'Storage Name,Filesystem Path,PI,Billing Contact,'
        'Technical Contact,Storage Groups'
    )
)
for usage in (
    AllocationUsage
        .objects
        .filter(
            storage_cluster='Storage2',
            usage_tb=0.0
        )
        .order_by('fileset_name')
    ):
    allocation = Allocation.objects.filter(pk=usage.external_key)[0]
    attributes = get_attributes(usage.external_key)
    storage_name = attributes.get("storage_name")
    if storage_name in storage_names or storage_name is None:
        continue
    storage_names.add(storage_name)
    # print(attributes)
    print(
        (
            f'{storage_name},{usage.filesystem_path},'
            f'{usage.sponsor_pi},{usage.billing_contact},'
            f'{attributes.get("technical_contact", "N/A")},'
            f'{"|".join(attributes.get("storage_groups"))}'
        )
    )
