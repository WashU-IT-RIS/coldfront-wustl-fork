import coldfront.plugins.qumulo.services.itsm.fields.transformers
import coldfront.plugins.qumulo.services.itsm.fields.validators

from coldfront.core.field_of_science.models import FieldOfScience

from coldfront.core.allocation.models import (
    Project,
    Allocation,
    AllocationAttribute,
    AllocationAttributeType,
    AllocationStatusChoice,
    AllocationUserStatusChoice,
    AllocationUser,
    Resource,
    User,
)

from coldfront.core.project.models import (
    Project,
    ProjectStatusChoice,
    ProjectUser,
    ProjectUserRoleChoice,
    ProjectUserStatusChoice,
)

from django.shortcuts import get_object_or_404

from coldfront.plugins.qumulo.services.itsm.itsm_client import ItsmClient

from coldfront.plugins.qumulo.services.itsm.fields.itsm_to_coldfront_fields_factory import (
    ItsmToColdfrontFieldsFactory,
)


class MigrateToColdfront:

    def by_fileset_alias(self, fileset_alias):
        itsm_result = self.__get_itsm_allocation_by_fileset_alias(fileset_alias)
        self.__execute(fileset_alias, itsm_result)

    def by_fileset_name(self, fileset_name):
        itsm_result = self.__get_itsm_allocation_by_fileset_name(fileset_name)
        self.__execute(fileset_name, itsm_result)

    def __execute(self, fileset_key, itsm_result):
        self.__validate_result_set(fileset_key, itsm_result)
        itsm_allocation = itsm_result[0]
        fields = ItsmToColdfrontFieldsFactory.get_fields(itsm_allocation)

        error_massages = []
        for field in fields:
            error_massages.append(field.validate())

        if any(error_massages):
            return error_massages

        pi_user = self.__create_user(fields)
        project = self.__create_project(fields, pi_user)
        allocation = self.__create_allocation(fields, project)
        self.__create_allocation_attributes(fields, allocation)
        return

    def __get_itsm_allocation_by_fileset_name(self, fileset_name):
        itsm_client = ItsmClient()
        itsm_allocation = itsm_client.get_fs1_allocation_by_fileset_name(fileset_name)
        return itsm_allocation

    def __get_itsm_allocation_by_fileset_alias(self, fileset_alias):
        itsm_client = ItsmClient()
        itsm_allocation = itsm_client.get_fs1_allocation_by_fileset_alias(fileset_alias)
        return itsm_allocation

    def __validate_result_set(self, fileset_key, itsm_result) -> bool:
        how_many = len(itsm_result)
        # ITSM does not return a respond code of 404 when the service provision record is not found.
        # Instead, it return an empty array.
        if how_many == 0:
            raise Exception(f'ITSM allocation was not found for "{fileset_key}"')

        if how_many > 1:
            raise Exception(
                f"Multiple ({how_many} total) ITSM allocations were found for {fileset_key}"
            )

        return True

    def __create_user(self, fields):
        username = None
        for field in fields:
            if field.entity != "user":
                continue

            for attribute in field.attributes:
                if attribute["name"] == "username":
                    username = field.value

        user = User.objects.create(
            username=username,
            password="WHAT IS THIS",
            email=f"{username}@wustl.edu",
        )
        return user

    # pi is the sponsor
    def __create_project(self, fields, pi_user):
        sponsor = None
        for field in fields:
            if field.entity != "project":
                continue

            for attribute in field.attributes:
                if attribute["name"] == "name":
                    sponsor = field.value

        # TODO should the field_of_science be other?
        description = f"project for {sponsor}"
        title = f"project for {sponsor}"
        project = Project.objects.create(
            field_of_science=FieldOfScience.objects.get(id="Other"),
            title=title,
            pi=pi_user,
            description=description,
            status=ProjectStatusChoice.objects.get(name="New"),
            force_review=False,
            requires_review=False,
        )

        ProjectUser.objects.create(
            user=pi_user,
            project=project,
            role=ProjectUserRoleChoice.objects.get(name="Manager"),
            status=ProjectUserStatusChoice.objects.get(name="Active"),
        )

        return project

    def __create_allocation(self, fields, project, user):

        allocation = Allocation.objects.create(
            project=project,
            justification="",
            quantity=1,
            status=AllocationStatusChoice.objects.get(name="Pending"),
        )

        active_status = AllocationUserStatusChoice.objects.get(name="Active")
        AllocationUser.objects.create(
            allocation=allocation, user=user, status=active_status
        )

        resource = Resource.objects.get(name="Storage2")
        allocation.resources.add(resource)

        # TODO
        # access_allocations = AllocationView.create_access_privileges(
        #    form_data, project, allocation
        # )

        # for access_allocation in access_allocations:
        #    access_users = AllocationUser.objects.filter(allocation=access_allocation)
        #    AclAllocations.create_ad_group_and_add_users(
        #        access_users, access_allocation
        #    )
        return allocation

    def __create_allocation_attributes(self, fields, allocation):
        for field in fields:
            if field.entity != "allocation_attribute":
                continue

            for attribute in field.attributes:
                if (
                    attribute["name"] == "name"
                ):  # TODO should be AllocationAttributeType
                    allocation_attribute_type = AllocationAttributeType.objects.get(
                        name=attribute["value"]
                    )
                    AllocationAttribute.objects.create(
                        allocation_attribute_type=allocation_attribute_type,
                        allocation=allocation,
                        value=field.value,
                    )
