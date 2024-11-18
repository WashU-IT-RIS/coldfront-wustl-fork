import coldfront.plugins.qumulo.services.itsm.fields.transformers
import coldfront.plugins.qumulo.services.itsm.fields.validators

from coldfront.core.field_of_science.models import FieldOfScience

from coldfront.plugins.qumulo.utils.acl_allocations import AclAllocations

from coldfront.plugins.qumulo.services.allocation_service import AllocationService

from coldfront.core.allocation.models import (
    Project,
    AllocationAttribute,
    AllocationAttributeType,
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

        # if any(error_massages):
        #    return error_massages
        pi_user = self.__create_user(fields)
        project = self.__create_project(pi_user)  # refactor method
        self.__create_project_user(project, pi_user)  # refactor method
        allocation = self.__create_allocation(fields, project, pi_user)
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
        # Instead, it returns an empty array.
        if how_many == 0:
            raise Exception(f'ITSM allocation was not found for "{fileset_key}"')

        if how_many > 1:
            raise Exception(
                f"Multiple ({how_many} total) ITSM allocations were found for {fileset_key}"
            )

        return True

    def __create_user(self, fields):
        username = self.__get_username(fields)
        user = User.objects.create(
            username=username,
            email=f"{username}@wustl.edu",
        )
        return user

    def __create_project(self, pi_user):
        description = f"project for {pi_user.username}"
        title = pi_user.username
        field_of_science = FieldOfScience.objects.get(description="Other")
        new_status = ProjectStatusChoice.objects.get(name="New")

        project = Project.objects.create(
            field_of_science=field_of_science,
            title=title,
            pi=pi_user,
            description=description,
            status=new_status,
            force_review=False,
            requires_review=False,
        )
        return project

    def __create_project_user(self, project, pi_user):
        pi_role = ProjectUserRoleChoice.objects.get(name="Manager")
        user_status = ProjectUserStatusChoice.objects.get(name="Active")

        project_user = ProjectUser.objects.create(
            user=pi_user,
            project=project,
            role=pi_role,
            status=user_status,
        )
        return project_user

    def __create_allocation(self, fields, project, pi_user):
        attributes_for_allocation = filter(
            lambda field: field.entity == "allocation", fields
        )

        allocation_data = {}
        allocation_data["project_pk"] = project.id
        allocation_data["ro_users"] = []
        for field in list(attributes_for_allocation):
            allocation_data.update(field.entity_item)

        service_result = AllocationService.create_new_allocation(
            allocation_data, pi_user
        )
        return service_result["allocation"]

    def __create_allocation_attributes(self, fields, allocation):
        allocation_attributes = filter(
            lambda field: field.entity == "allocation_attribute"
            and field.value is not None,
            fields,
        )
        for field in list(allocation_attributes):
            for attribute in field.attributes:
                if (
                    attribute["name"] == "allocation_attribute_type__name"
                ):  # TODO should be AllocationAttributeType
                    allocation_attribute_type = AllocationAttributeType.objects.get(
                        name=attribute["value"]
                    )
                    AllocationAttribute.objects.get_or_create(
                        allocation_attribute_type=allocation_attribute_type,
                        allocation=allocation,
                        value=field.value,
                    )

    def __get_username(self, fields):
        username = None
        for field in fields:
            username = field.get_username()
            if username is not None:
                break
        return username
