from django.db.models import Q
from django.db.models import OuterRef, Subquery

from coldfront.core.allocation.models import Allocation, AllocationAttribute
from coldfront.core.resource.models import Resource
from coldfront.core.project.models import Project

class BillingResultSet():
    def retrieve_billing_result_set(billing_cycle, begin_billing, end_billing):
        resource = Resource.objects.get(name="Storage2")
        allocation_list = Allocation.objects.filter(resources=resource)
        project = Project.objects.all()

        billing_cycle_sub_query = AllocationAttribute.objects.filter(
        allocation=OuterRef("pk"), allocation_attribute_type__name="billing_cycle",
        ).values("value")[:1]
        cost_center_sub_query = AllocationAttribute.objects.filter(
        allocation=OuterRef("pk"), allocation_attribute_type__name="cost_center"
        ).values("value")[:1]
        subsidized_sub_query = AllocationAttribute.objects.filter(
        allocation=OuterRef("pk"), allocation_attribute_type__name="subsidized"
        ).values("value")[:1]
        billing_exempt_sub_query = AllocationAttribute.objects.filter(
        allocation=OuterRef("pk"), allocation_attribute_type__name="billing_exempt"
        ).values("value")[:1]
        pi_subquery = Project.objects.filter(allocation=OuterRef("pk")).values('pi')[:1]
        
        
        allocation_list = allocation_list.annotate(billing_cycle=Subquery(billing_cycle_sub_query), 
                                                   cost_center=Subquery(cost_center_sub_query), 
                                                   subsidized=Subquery(subsidized_sub_query),
                                                   billing_exempt=Subquery(billing_exempt_sub_query),
                                                   pi=Subquery(pi_subquery),)
        breakpoint()

        return allocation_list