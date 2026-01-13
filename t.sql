SELECT "allocation_allocation"."id", "allocation_allocation"."created", "allocation_allocation"."modified", "allocation_allocation"."project_id", "allocation_allocation"."status_id", "allocation_allocation"."quantity", "allocation_allocation"."start_date", "allocation_allocation"."end_date", "allocation_allocation"."justification", "allocation_allocation"."description", "allocation_allocation"."is_locked", "allocation_allocation"."is_changeable" 
FROM "allocation_allocation" 
INNER JOIN "allocation_allocationattribute" ON ("allocation_allocation"."id" = "allocation_allocationattribute"."allocation_id") 
INNER JOIN "allocation_allocationattributetype" ON ("allocation_allocationattribute"."allocation_attribute_type_id" = "allocation_allocationattributetype"."id") 
INNER JOIN "allocation_allocation_resources" ON ("allocation_allocation"."id" = "allocation_allocation_resources"."allocation_id") 
INNER JOIN "resource_resource" ON ("allocation_allocation_resources"."resource_id" = "resource_resource"."id") 
WHERE ("allocation_allocationattributetype"."name" = 'storage_name' 
    AND "allocation_allocationattribute"."value" = 'DuplicateName' 
    AND "resource_resource"."name" = 'Storage2');
