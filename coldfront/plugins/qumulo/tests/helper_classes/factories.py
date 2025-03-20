import factory

from coldfront.core.project.models import ProjectAttribute
from coldfront.core.resource.models import ResourceType, Resource
from coldfront.core.test_helpers.factories import (
    AllocationFactory,
    AllocationStatusChoiceFactory,
    FieldOfScienceFactory,
    ProjectAttributeFactory,
    ProjectFactory,
    ProjectStatusChoiceFactory,
    ResourceFactory,
    ResourceTypeFactory,
    UserFactory,
)


class RISProjectFactory(ProjectFactory):
    pi = factory.SubFactory(UserFactory)
    title = factory.LazyAttribute(lambda project: project.pi.username)
    description = factory.LazyAttribute(
        lambda project: f"project for {project.pi.username}"
    )
    status = factory.SubFactory(ProjectStatusChoiceFactory, name="New")
    field_of_science = factory.SubFactory(FieldOfScienceFactory, description="Other")
    force_review = False
    requires_review = True


class RISAllocationFactory(AllocationFactory):
    project = factory.SubFactory(RISProjectFactory)

    class Params:
        storage2 = (
            factory.Trait(
                justification="",
                status=factory.SubFactory(
                    AllocationStatusChoiceFactory, name="Pending"
                ),
            ),
        )
        read_write_group = (
            factory.Trait(
                justification="RW Users",
                status=factory.SubFactory(AllocationStatusChoiceFactory, name="Active"),
            ),
        )
        read_only_group = (
            factory.Trait(
                justification="RO Users",
                status=factory.SubFactory(AllocationStatusChoiceFactory, name="Active"),
            ),
        )


class Storage2Factory(RISAllocationFactory):
    storage2 = True

    @factory.post_generation
    def resources(self, create, extracted, **kwargs):
        if not create:
            return None

        resource = ResourceFactory(
            name="Storage2",
            resource_type=ResourceTypeFactory(name="Storage"),
        )
        self.resources.add(resource)


class ReadWriteGroupFactory(RISAllocationFactory):
    read_write_group = True

    @factory.post_generation
    def resources(self, create, extracted, **kwargs):
        if not create:
            return None

        resource = ResourceFactory(
            name="rw",
            resource_type=ResourceTypeFactory(name="ACL"),
        )
        self.resources.add(resource)


class ReadOnlyGroupFactory(RISAllocationFactory):
    read_only_group = True

    @factory.post_generation
    def resources(self, create, extracted, **kwargs):
        if not create:
            return None

        resource = ResourceFactory(
            name="ro",
            resource_type=ResourceTypeFactory(name="ACL"),
        )
        self.resources.add(resource)

