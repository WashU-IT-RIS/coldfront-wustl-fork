import factory

from factory.django import DjangoModelFactory

from coldfront.core.allocation.models import Allocation
from coldfront.core.project.models import ProjectAttribute
from coldfront.core.resource.models import ResourceType, Resource
from coldfront.core.test_helpers.factories import (
    AllocationStatusChoiceFactory,
    FieldOfScienceFactory,
    ProjectFactory,
    ProjectStatusChoiceFactory,
    ResourceFactory,
    ResourceTypeFactory,
    UserFactory,
)


class RisProjectFactory(ProjectFactory):
    pi = factory.SubFactory(UserFactory)
    title = factory.LazyAttribute(lambda project: project.pi.username)
    description = factory.LazyAttribute(
        lambda project: f"project for {project.pi.username}"
    )
    status = factory.SubFactory(ProjectStatusChoiceFactory, name="New")
    field_of_science = factory.SubFactory(FieldOfScienceFactory, description="Other")
    force_review = False
    requires_review = True


class RisAllocationFactory(DjangoModelFactory):
    class Meta:
        model = Allocation

    justification = factory.Faker("sentence")
    status = factory.SubFactory(AllocationStatusChoiceFactory)
    project = factory.SubFactory(RisProjectFactory)
    is_changeable = True

    class Params:
        storage2 = factory.Trait(
            justification="",
            status=factory.SubFactory(AllocationStatusChoiceFactory, name="Active"),
        )

        read_write_group = factory.Trait(
            justification="RW Users",
            status=factory.SubFactory(AllocationStatusChoiceFactory, name="Active"),
        )

        read_only_group = factory.Trait(
            justification="RO Users",
            status=factory.SubFactory(AllocationStatusChoiceFactory, name="Active"),
        )


class Storage2Factory(RisAllocationFactory):
    storage2 = True

    @factory.post_generation
    def resources(self, create, extracted, **kwargs):
        if not create:
            return None

        resources = extracted or (
            ResourceFactory(
                name="Storage2", resource_type=ResourceTypeFactory(name="Storage")
            ),
        )
        self.resources.add(*resources)


class ReadWriteGroupFactory(RisAllocationFactory):
    read_write_group = True

    @factory.post_generation
    def resources(self, create, extracted, **kwargs):
        if not create:
            return None

        resources = extracted or (
            ResourceFactory(name="rw", resource_type=ResourceTypeFactory(name="ACL")),
        )
        self.resources.add(*resources)


class ReadOnlyGroupFactory(RisAllocationFactory):
    read_only_group = True

    @factory.post_generation
    def resources(self, create, extracted, **kwargs):
        if not create:
            return None

        resources = extracted or (
            ResourceFactory(name="rw", resource_type=ResourceTypeFactory(name="ACL")),
        )
        self.resources.add(*resources)
