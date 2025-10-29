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
    rate = 100
    unit_rate = 1
    unit = "TB"
    cycle = "monthly"

    class Params:
        archive_service = factory.Trait(
            model_name="consumption",
            model_display_name="Archive Service",
            model_description="Archive Service Description",
            rate=3.15,
            tier_name="archive",
        )
        active_service = factory.Trait(
            model_name="consumption",
            model_display_name="Active Service",
            model_description="Active Service Description",
            rate=6.50,
            tier_name="active",
        )
        current_service_rate = factory.Trait(
            start_date=factory.LazyFunction(
                lambda: date.today().replace(day=1, month=1)
            ),
            end_date=factory.LazyFunction(
                lambda: date.today().replace(day=31, month=12)
            ),
        )
        previous_service_rate = factory.Trait(
            start_date=factory.LazyFunction(lambda: date(2023, 7, 1)),
            end_date=factory.LazyFunction(lambda: date(2024, 6, 30)),
        )


# Example usage:
# service_rate_category = ServiceRateCategoryFactory()  # Creates a ServiceRateCategory instance with default values
# archive_category = ServiceRateCategoryFactory(archive_service=True)  # Creates an archive service category
# active_category = ServiceRateCategoryFactory(active_service=True)  # Creates an active service category
# from coldfront.plugins.integratedbilling.factories import ServiceRateCategoryFactory
# current_archive_rates = ServiceRateCategoryFactory(current_service_rate=True, archive_service=True)  # Creates a category with current rates
