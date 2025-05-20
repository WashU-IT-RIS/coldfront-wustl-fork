from django.db.models import Q
from django.db.models import OuterRef, Subquery
from django.utils.timezone import make_aware

from coldfront.core.allocation.models import Allocation, AllocationAttribute, AllocationAttributeType, AllocationUser, AllocationAttributeUsage
from coldfront.core.resource.models import Resource
from coldfront.core.project.models import Project

from datetime import datetime

class BillingResultSet():
    def retrieve_billing_result_set(billing_cycle, begin_billing, end_billing):
        date_format = "%Y-%m-%d %H:%M:%S"
        begin_billing_datetime = datetime.strptime(begin_billing, date_format)
        end_billing_datetime = datetime.strptime(end_billing, date_format)
        allocation_list = Allocation.objects.filter(Q(resources__name="Storage2") & Q(start_date__lte=begin_billing_datetime) | Q(end_date__gte=end_billing_datetime))
        project_ids = Allocation.objects.filter(resources__name="Storage2").values_list('project', flat=True)
        
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
        project_attribute_pi = allocation_list.values('project')
        usages = AllocationAttributeUsage.history.filter(allocation_attribute__allocation__in=allocation_list, 
                                                         allocation_attribute__allocation_attribute_type__name="storage_quota", 
                                                         allocation_attribute__allocation__status__name="Active", 
                                                         history_date__range=(make_aware(begin_billing_datetime), make_aware(end_billing_datetime))).values("value")[:1]
        #breakpoint()
        
        allocation_list = allocation_list.annotate(billing_cycle=Subquery(billing_cycle_sub_query), 
                                                   cost_center=Subquery(cost_center_sub_query), 
                                                   subsidized=Subquery(subsidized_sub_query),
                                                   billing_exempt=Subquery(billing_exempt_sub_query),
                                                   #pi=project_attribute_pi.values("project__pi"),
                                                   usage=usages).values('billing_cycle','cost_center','subsidized','billing_exempt','usage')

        return allocation_list