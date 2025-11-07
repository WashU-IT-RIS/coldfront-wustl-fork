from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttribute,
    AllocationAttributeUsage,
)

from django.db.models.expressions import OuterRef, Subquery


sub_queries = {}

for key in [
    "storage_name",
    "fileset_name",
    "department_number",
]:
    sub_queries[key] = Subquery(
        AllocationAttribute.objects.filter(
            allocation=OuterRef("pk"),
            allocation_attribute_type__name=key,
        ).values("value")[:1]
    )

usage_bytes = Subquery(
    AllocationAttributeUsage.objects.filter(
        allocation_attribute__allocation=OuterRef("pk"),
        allocation_attribute__allocation_attribute_type__name="storage_quota",
    ).values("value")[:1]
)

sub_queries["usage_bytes"] = usage_bytes

Allocation.objects.parents().active_storage().annotate(**sub_queries).select_related(
    "project__pi"
).values(
    "pk",
    "department_number",
    "project__pi__username",
    "usage_bytes",
)
