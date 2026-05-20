from datetime import date
import factory
from factory.django import DjangoModelFactory
from coldfront.plugins.integratedbilling.models import ServiceRateCategory


class ServiceRateCategoryFactory(DjangoModelFactory):
    class Meta:
        model = ServiceRateCategory

    model_name = factory.Sequence(lambda n: f"model_name_{n}")
    model_display_name = factory.Sequence(lambda n: f"Model Display Name {n}")
    model_description = factory.Sequence(lambda n: f"Model Description {n}")
    start_date = factory.LazyFunction(lambda: date.today())
    end_date = factory.LazyFunction(lambda: date.today())
    rate = factory.Faker("pydecimal", left_digits=2, right_digits=2, positive=True)
    unit_rate = factory.Faker("pyint", min=1, max=9)
    unit = "TB"
    cycle = factory.Iterator(["monthly", "yearly"])
    tier_name = factory.Iterator(["Archive", "Active"])

    class Params:
        archive_service = factory.Trait(
            model_name="consumption",
            model_display_name="Archive Service",
            model_description="Archive Service Description",
            rate=3.15,
            unit=1,
            unit="TB",
            tier_name="Archive",
            cycle="monthly",
        )
        active_service = factory.Trait(
            model_name="consumption",
            model_display_name="Active Service",
            model_description="Active Service Description",
            rate=6.50,
            unit=1,
            unit="TB",
            tier_name="Active",
            cycle="monthly",
        )

        # TODO: Instead of hardcoding the dates, we should calculate them based on the current date to ensure they are always relevant.
        current_service_rate = factory.Trait(
            start_date=factory.LazyFunction(lambda: date(2025, 9, 1)),
            end_date=factory.LazyFunction(lambda: date(2026, 6, 30)),
        )

        previous_service_rate = factory.Trait(
            start_date=factory.LazyFunction(lambda: date(2023, 7, 1)),
            end_date=factory.LazyFunction(lambda: date(2024, 6, 30)),
        )


class BillableUserFactory(factory.Factory):
    class Meta:
        model = "integratedbilling.BillableUser"

    user = factory.SubFactory("coldfront.core.factories.UserFactory")


# Example usage:
# from coldfront.plugins.integratedbilling.factories import ServiceRateCategoryFactory

# service_rate_category = (
#     ServiceRateCategoryFactory()
# )  # Creates a ServiceRateCategory instance with default values

# archive_category = ServiceRateCategoryFactory(
#     archive_service=True
# )  # Creates an archive service category

# active_category = ServiceRateCategoryFactory(
#     active_service=True
# )  # Creates an active service category

# current_archive_rates = ServiceRateCategoryFactory(
#     current_service_rate=True, archive_service=True
# )  # Creates a category with current rates

# previous_active_rates = ServiceRateCategoryFactory(
#     previous_service_rate=True, active_service=True
# )  # Creates a category with previous rates
