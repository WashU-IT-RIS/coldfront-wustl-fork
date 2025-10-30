from datetime import datetime
from coldfront.core.billing.models import MonthlyStorageBilling
from coldfront.plugins.integratedbilling.models import ServiceRateCategory

# TODO: Move to config?
SUBSIDIZED_AMOUNT_TB = (
    5  # (float): indicates the amount of TB subsidized per allocation usage
)


def get_billing_objects(usages: list, report_date: str) -> list[MonthlyStorageBilling]:
    billing_objects = []
    for billing_object in usages:
        tier_name = "active"  # billing_object.service_name
        model_name = billing_object.service_rate_category
        billing_cycle = billing_object.billing_cycle
        print(
            f"Calculating cost for Usage ID {billing_object.id}: Tier={tier_name}, Model={model_name}, Cycle={billing_cycle}"
        )
        tier_name = "active"  # billing_object.tier
        model_name = billing_object.service_rate_category
        billing_cycle = billing_object.billing_cycle

        rate_category = (
            ServiceRateCategory.current_rates.all()
            .for_tier(tier_name)
            .for_cycle(billing_cycle)
            .get()
        )
        billing_object.calculated_cost = __calculate_rate(billing_object, rate_category)

        billing_object.delivery_date = report_date  # (str): indicates the beginning date of the service for monthly billing (ex. 2024-05-01)
        billing_object.tier = (
            rate_category.tier_name
        )  # (str): indicates the service tier of the allocation (ex. Active, Archive)
        billing_object.billing_unit = (
            rate_category.unit
        )  # (str): indicates the billing unit of the service (ex. TB)
        billing_object.unit_rate = (
            rate_category.rate
        )  # (str): indicates the unit rate of the service
        billing_object.billing_amount = (
            billing_object.calculated_cost
        )  # (str): indicates the total dollar amount of the service for the monthly billing
        billing_objects.append(billing_object)

    return billing_objects


def __calculate_rate(
    billing_object: MonthlyStorageBilling, rate_category: ServiceRateCategory
) -> float:
    usage_tb = billing_object.usage_tb
    if billing_object.subsidized:
        usage_tb = max(0, usage_tb - SUBSIDIZED_AMOUNT_TB)

    if rate_category:
        return usage_tb * rate_category.rate
    return 0.0
