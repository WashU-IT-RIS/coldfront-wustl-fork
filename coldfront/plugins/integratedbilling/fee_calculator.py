from datetime import date, timedelta
from decimal import Decimal
from coldfront.core.billing.models import MonthlyStorageBilling
from coldfront.plugins.integratedbilling.models import ServiceRateCategory

# TODO: Move to config?
SUBSIDIZED_AMOUNT_TB = Decimal(
    5.0  # (float): indicates the amount of TB subsidized per allocation usage
)


def get_billing_objects(
    usages: list[MonthlyStorageBilling],
) -> list[MonthlyStorageBilling]:
    billing_objects = []
    for billing_object in usages:
        # print(f"Processing Usage ID {billing_object.id} with {billing_object.usage_tb} TB used.")
        # TODO: rejecting zero and negative usages should be handled by the Billing.monthly_billable queryset filter
        if billing_object.usage_tb <= Decimal("0.0"):
            print(
                f"Warning: Usage TB for AllocationUsage ID {billing_object.id} (fileset {billing_object.fileset_name}) is negative. Skipping."
            )
            continue

        billing_object.billable_usage_tb = billing_object.usage_tb
        if billing_object.subsidized:
            billing_object.billable_usage_tb = max(
                Decimal("0.0"), (billing_object.usage_tb - SUBSIDIZED_AMOUNT_TB)
            )

        if billing_object.billable_usage_tb == Decimal("0.0"):
            continue

        tier_name = "active"  # billing_object.tier
        model_name = "consumption"  # billing_object.service_rate_category
        billing_cycle = billing_object.billing_cycle

        rate_category = (
            ServiceRateCategory.rates.for_date(billing_object.usage_date)
            .for_tier(tier_name)
            .for_cycle(billing_cycle)
            .for_model(model_name)
            .get()
        )

        billing_object.calculated_cost = calculate_fee(billing_object, rate_category)

        if billing_object.calculated_cost <= Decimal("0.00"):
            continue

        billing_object.delivery_date = __get_delivery_date(
            billing_object.usage_date
        )  # (str): indicates the beginning date of the service for monthly billing (ex. 2024-05-01)
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


def calculate_fee(
    billing_object: MonthlyStorageBilling, rate_category: ServiceRateCategory
) -> float:
    return round(billing_object.billable_usage_tb * rate_category.rate, 2)


def __get_delivery_date(usage_date: date) -> str:
    first_of_previous_month = (usage_date.replace(day=1) - timedelta(days=1)).replace(
        day=1
    )
    return first_of_previous_month.strftime("%Y-%m-%d")
