from django.db.models import OuterRef, Subquery
from django.utils.timezone import make_aware

from coldfront.core.allocation.models import Allocation, AllocationAttribute, AllocationAttributeUsage
from coldfront.core.project.models import Project

from datetime import datetime

class BillingResultSet():
    def retrieve_billing_result_set(billing_cycle, begin_billing, end_billing):
        date_format = "%Y-%m-%d %H:%M:%S"
        begin_billing_datetime = datetime.strptime(begin_billing, date_format)
        end_billing_datetime = datetime.strptime(end_billing, date_format)
        allocation_list = Allocation.objects.filter(resources__name="Storage2", start_date__lte=begin_billing_datetime, end_date__gte=end_billing_datetime)
        breakpoint()
        
        billing_cycle_sub_query = AllocationAttribute.objects.filter(
        allocation=OuterRef("pk"), allocation_attribute_type__name="billing_cycle",
        ).values("value")
        cost_center_sub_query = AllocationAttribute.objects.filter(
        allocation=OuterRef("pk"), allocation_attribute_type__name="cost_center"
        ).values("value")
        subsidized_sub_query = AllocationAttribute.objects.filter(
        allocation=OuterRef("pk"), allocation_attribute_type__name="subsidized"
        ).values("value")
        billing_exempt_sub_query = AllocationAttribute.objects.filter(
        allocation=OuterRef("pk"), allocation_attribute_type__name="billing_exempt"
        ).values("value")
        pi_sub_query = Project.objects.filter(allocation__in=allocation_list).values('pi__username')
        breakpoint()
        usages_sub_query = AllocationAttributeUsage.history.filter(allocation_attribute__allocation__in=allocation_list, 
                                                        allocation_attribute__allocation_attribute_type__name="storage_quota",
                                                        history_date__date__range=(begin_billing_datetime, end_billing_datetime)).values("value")
        breakpoint()
        
        allocation_list = allocation_list.annotate(billing_cycle=Subquery(billing_cycle_sub_query), 
                                                   cost_center=Subquery(cost_center_sub_query), 
                                                   billing_exempt=Subquery(billing_exempt_sub_query),
                                                   subsidized=Subquery(subsidized_sub_query),
                                                   pi=Subquery(pi_sub_query),
                                                   usage=Subquery(usages_sub_query)).values('billing_cycle','cost_center','subsidized','billing_exempt','usage', 'pi')
        
        return list(allocation_list)
    