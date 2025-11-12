import factory
from faker import Faker
from django.utils import timezone
from coldfront.core.billing.models import AllocationUsage

fake = Faker()

class AllocationUsageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AllocationUsage

    external_key = factory.Sequence(lambda n: n)
    source = factory.LazyAttribute(lambda _: fake.random_element(elements=['ITSM', 'ColdFront', 'Other']))
    tier = factory.LazyAttribute(lambda _: fake.random_element(elements=['Active', 'Archive']))
    filesystem_path = factory.LazyAttribute(lambda _: fake.random_element(elements=['/filesystem/filesetA', '/filesystem/filesetB', '/filesystem/filesetC', '/filesystem/filesetD']))
    sponsor_pi = factory.LazyAttribute(lambda _: fake.name())
    billing_contact = factory.LazyAttribute(lambda _: fake.email())
    fileset_name = factory.LazyAttribute(lambda _: fake.word())
    status = factory.LazyAttribute(lambda _: fake.random_element(elements=['new', 'active', 'pending', 'jenkins error']))
    service_rate_category = factory.LazyAttribute(lambda _: fake.word())
    usage_tb = factory.LazyAttribute(lambda _: str(fake.pydecimal(left_digits=2, right_digits=6, positive=True)))
    funding_number = factory.LazyAttribute(lambda _: fake.bothify(text='??####'))
    exempt = factory.LazyAttribute(lambda _: fake.boolean())
    subsidized = factory.LazyAttribute(lambda _: fake.boolean())
    is_condo_group = factory.LazyAttribute(lambda _: fake.boolean())
    parent_id_key = factory.Sequence(lambda n: n)
    quota = factory.LazyAttribute(lambda _: str(fake.random_int(min=1, max=100)))
    billing_cycle = factory.LazyAttribute(lambda _: fake.random_element(elements=['monthly', 'prepaid']))
    usage_date = factory.LazyAttribute(lambda _: fake.date_this_year())
    storage_cluster = factory.LazyAttribute(lambda _: fake.random_element(elements=['Storage1', 'Storage2', 'Storage3']))
