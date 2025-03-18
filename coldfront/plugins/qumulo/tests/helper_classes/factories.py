import factory

from coldfront.core.test_helpers.factories import (
    AllocationFactory,
    AllocationStatusChoiceFactory,
    FieldOfScienceFactory,
    ProjectFactory,
    ProjectStatusChoiceFactory,
    ResourceFactory,
    ResourceTypeFactory,
    UserFactory,
)

from coldfront.core.test_helpers.factories import field_of_science_provider

field_of_science_provider.add_element("Other")


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
    justification = ""
    status = factory.SubFactory(AllocationStatusChoiceFactory)


class Storage2Factory(RISAllocationFactory):

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

    @factory.post_generation
    def resources(self, create, extracted, **kwargs):
        if not create:
            return None

        resource = ResourceFactory(
            name="ro",
            resource_type=ResourceTypeFactory(name="ACL"),
        )
        self.resources.add(resource)
