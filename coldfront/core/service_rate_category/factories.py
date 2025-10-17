import factory
from coldfront.core.service_rate_category import models


class ServiceRateCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ServiceRateCategory

    service = factory.SubFactory(
        "coldfront.core.service_rate_category.factories.ServiceFactory"
    )
    model_name = factory.Faker("word")
    model_display_name = factory.Faker("word")
    model_description = factory.Faker("sentence")
    start_date = factory.Faker("date_this_decade")
    end_date = factory.Faker("date_this_decade")


class ServiceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Service

    name = factory.Faker("word")
    description = factory.Faker("sentence")


class ServiceRateCategoryTierFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ServiceRateCategoryTier

    name = factory.Faker("word")
    rate = factory.Faker("random_int", min=1, max=1000)
    unit_rate = factory.Faker("random_int", min=1, max=100)
    unit = factory.Faker("word")
    cycle = factory.Faker("word")
    service_rate_category = factory.SubFactory(ServiceRateCategoryFactory)
