from typing import Any
from coldfront.core.field_of_science.models import FieldOfScience

from coldfront.plugins.qumulo.services.allocation_service import AllocationService

from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttribute,
    AllocationAttributeType,
    Project,
    User,
    Resource,
)

from coldfront.core.project.models import (
    Project,
    ProjectAttribute,
    ProjectAttributeType,
    ProjectStatusChoice,
    ProjectUser,
    ProjectUserRoleChoice,
    ProjectUserStatusChoice,
)

from coldfront.plugins.qumulo.services.itsm.itsm_client import ItsmClient

from coldfront.plugins.qumulo.services.itsm.fields.itsm_to_coldfront_fields_factory import (
    ItsmToColdfrontFieldsFactory,
)

import json, os


class MigrateToColdfront:

    __overrides: dict[str, Any] = {}

    def __init__(self, dry_run: bool = False) -> None:
        self.dry_run = dry_run

    def by_fileset_alias(self, fileset_alias: str, resource_name: str) -> str:
        itsm_result = self.__get_itsm_allocation_by_fileset_alias(fileset_alias)
        result = self.__create_by(fileset_alias, itsm_result, resource_name)
        return result

    def by_fileset_name(self, fileset_name: str, resource_name: str) -> str:
        itsm_result = self.__get_itsm_allocation_by_fileset_name(fileset_name)
        result = self.__create_by(fileset_name, itsm_result, resource_name)
        return result

    def by_storage_provision_name(
        self, storage_provision_name: str, resource_name: str
    ) -> str:
        itsm_result = self.__get_itsm_allocation_by_storage_provision_name(
            storage_provision_name
        )
        result = self.__create_by(storage_provision_name, itsm_result, resource_name)
        return result

    def set_override(self, field_name: str, value: any) -> None:
        overridable_fields = ItsmToColdfrontFieldsFactory.get_overridable_attributes()
        if field_name not in overridable_fields:
            raise Exception(
                f"{field_name} is not an overridable field. Overridable fields are: {overridable_fields}"
            )

        self.__overrides.update({field_name: value})

    # Private Methods
    def __create_by(self, key: str, itsm_result: str, resource_name: str) -> str:
        self.__validate_itsm_result_set(key, itsm_result)
        itsm_allocation = itsm_result[0]
        fields = ItsmToColdfrontFieldsFactory.get_fields(
            itsm_allocation, self.__overrides
        )

        field_error_messages = {}
        field_warning_messages = {}
        for field in fields:
            validation_messages = field.validate()
            if validation_messages:
                if field.should_warn_not_error():
                    if not field.itsm_attribute_name in field_warning_messages:
                        field_warning_messages[field.itsm_attribute_name] = []

                    field_warning_messages[
                        field.itsm_attribute_name
                    ] += validation_messages
                    continue

                if not field.itsm_attribute_name in field_error_messages:
                    field_error_messages[field.itsm_attribute_name] = []

                field_error_messages[field.itsm_attribute_name] += validation_messages

        if field_error_messages:
            messages = {
                "errors": field_error_messages,
                "warnings": field_warning_messages,
            }
            raise Exception(messages)

        if self.dry_run:
            return {
                f"validation checks for {key}": "successful",
                "itsm_allocation": itsm_allocation,
                "warning_messages": field_warning_messages,
            }

        resource_type = self.__get_resource(resource_name)
        pi_user = self.__get_or_create_user(fields)
        project, created = self.__get_or_create_project(pi_user)
        if created:
            self.__create_project_user(project, pi_user)
            self.__create_project_attributes(fields, project)

        allocation, dir_projects = self.__create_allocation(
            key, fields, project, pi_user, resource_type
        )
        self.__create_allocation_attributes(fields, allocation)

        result = {
            "allocation_id": allocation.id,
            "project_id": project.id,
            "pi_user_id": pi_user.id,
            "warning_messages": field_warning_messages,
        }

        if dir_projects is None or dir_projects == {}:
            return result

        sub_allocations = self.__create_sub_allocations(
            dir_projects, parent_allocation=allocation, fields=fields
        )
        result["sub_allocations"] = sub_allocations

        return result

    def __get_itsm_allocation_by_fileset_name(self, fileset_name: str) -> str:
        itsm_client = ItsmClient()
        itsm_allocation = itsm_client.get_fs1_allocation_by_fileset_name(fileset_name)
        return itsm_allocation

    def __get_itsm_allocation_by_fileset_alias(self, fileset_alias: str) -> list:
        itsm_client = ItsmClient()
        itsm_allocation = itsm_client.get_fs1_allocation_by_fileset_alias(fileset_alias)
        return itsm_allocation

    def __get_itsm_allocation_by_storage_provision_name(
        self, storage_provision_name: str
    ) -> list:
        itsm_client = ItsmClient()
        itsm_allocation = itsm_client.get_fs1_allocation_by_storage_provision_name(
            storage_provision_name
        )
        return itsm_allocation

    def __validate_itsm_result_set(self, key: str, itsm_result: list) -> bool:
        how_many = len(itsm_result)
        # ITSM does not return a respond code of 404 when the service provision record is not found.
        # Instead, it returns an empty array.
        if how_many == 0:
            raise Exception(f"ITSM active allocation was not found for {key}")

        if how_many > 1:
            raise Exception(
                f"Multiple ({how_many} total) ITSM active allocations were found for {key}"
            )

        return True

    def __get_resource(self, resource_name: str) -> Resource:
        resource = Resource.objects.get(name=resource_name)
        if not resource:
            raise Exception("Qumulo resource not found")
        return resource

    def __get_or_create_user(self, fields: list) -> User:
        username = self.__get_username(fields)
        # TODO get email by washu key
        # user_email = self.__get_email_from_ad_lookup(username)
        # if email is None:
        #    raise Exception(f"No email found for user {username} in AD Lookup")

        user, _ = User.objects.get_or_create(
            username=username,
            email=f"{username}@wustl.edu",
        )
        return user

    def __get_or_create_project(self, pi_user: User) -> Project:
        project_query = Project.objects.filter(
            title=pi_user.username,
            pi=pi_user,
        )
        if project_query.exists():
            return (project_query[0], False)

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
        return (project, True)

    def __create_project_user(self, project: Project, pi_user: User) -> ProjectUser:
        pi_role = ProjectUserRoleChoice.objects.get(name="Manager")
        user_status = ProjectUserStatusChoice.objects.get(name="Active")

        project_user = ProjectUser.objects.create(
            user=pi_user,
            project=project,
            role=pi_role,
            status=user_status,
        )
        return project_user

    def __create_project_attributes(self, fields: list, project: Project) -> None:
        project_attributes = filter(
            lambda field: field.entity == "project_attribute"
            and field.value is not None,
            fields,
        )
        for field in list(project_attributes):
            for attribute in field.attributes:
                if attribute["name"] == "proj_attr_type":
                    project_attribute_type = ProjectAttributeType.objects.get(
                        name=attribute["value"]
                    )
                    ProjectAttribute.objects.get_or_create(
                        proj_attr_type=project_attribute_type,
                        project=project,
                        value=field.value,
                    )

    def __create_allocation(
        self,
        key: str,
        fields: list,
        project: Project,
        pi_user: User,
        resource: Resource,
    ) -> str:
        attributes_for_allocation = filter(
            lambda field: field.entity == "allocation_form", fields
        )

        allocation_data = self.__get_allocation_data_from_fields(
            attributes_for_allocation, key, resource, project
        )
        service_result = AllocationService.create_new_allocation(
            form_data=allocation_data, user=pi_user
        )
        return service_result["allocation"], allocation_data.get("dir_projects")

    def __create_allocation_attributes(
        self, fields: list, allocation: Allocation
    ) -> None:
        allocation_attributes = filter(
            lambda field: field.entity == "allocation_attribute"
            and field.value is not None,
            fields,
        )

        for field in list(allocation_attributes):
            for attribute in field.attributes:
                if attribute["name"] == "allocation_attribute_type__name":
                    allocation_attribute_type = AllocationAttributeType.objects.get(
                        name=attribute["value"]
                    )
                    AllocationAttribute.objects.update_or_create(
                        allocation_attribute_type=allocation_attribute_type,
                        allocation=allocation,
                        defaults={"value": field.value},
                    )

    def __get_username(self, fields: list) -> str:
        for field in fields:
            username = field.get_username()
            if username is not None:
                return username

        return None

    def __create_sub_allocations(
        self, dir_projects: dict, parent_allocation: Allocation, fields: list
    ) -> None:
        sub_allocations = []
        for sub_allocation_name, users in dir_projects.items():
            purified_sub_allocation_name = sub_allocation_name.strip()
            sub_allocation_form_data = self.__get_sub_allocation_form_data(
                sub_allocation_name=purified_sub_allocation_name,
                users=users,
                parent_allocation=parent_allocation,
                fields=fields,
            )

            sub_allocations.append(
                AllocationService.create_sub_allocation(
                    sub_allocation_form_data=sub_allocation_form_data,
                    pi_user=parent_allocation.project.pi,
                    parent_allocation=parent_allocation,
                )
            )
        return sub_allocations

    def __get_allocation_path(self, key, resource: Resource) -> str:
        # "example_lab/foo/bar_active" -> "bar"
        seed_path = key.split("_active")[0].rsplit("/", 1)[-1]
        qumulo_info = json.loads(os.environ.get("QUMULO_INFO"))
        base_path = qumulo_info[resource.name]["path"]
        return f"{base_path}/{seed_path}"

    def __get_allocation_data_from_fields(
        self, attributes_for_allocation, key, resource: Resource, project: Project
    ) -> dict:
        allocation_data = {}
        allocation_data["project_pk"] = project.id
        allocation_data["ro_users"] = []
        allocation_data["storage_type"] = resource.name
        for field in list(attributes_for_allocation):
            allocation_data.update(field.entity_item)

        allocation_data["storage_filesystem_path"] = self.__get_allocation_path(
            key, resource
        )
        allocation_data["storage_export_path"] = self.__get_allocation_path(
            key, resource
        )
        return allocation_data

    def __get_sub_allocation_form_data(
        self,
        sub_allocation_name: str,
        users: dict,
        parent_allocation: Allocation,
        fields: list,
    ) -> dict:
        sub_allocation_form_data = {}
        sub_allocation_form_data["project_pk"] = parent_allocation.project.id
        sub_allocation_form_data["storage_name"] = sub_allocation_name
        sub_allocation_form_data["storage_type"] = parent_allocation.resources.get(
            resource_type__name="Storage"
        ).name
        sub_allocation_form_data["storage_filesystem_path"] = sub_allocation_name
        sub_allocation_form_data["storage_export_path"] = sub_allocation_name
        for field in [
            sub_allocation_field
            for sub_allocation_field in fields
            if sub_allocation_field.entity == "sub_allocation_form"
        ]:
            sub_allocation_form_data.update(field.entity_item)

        sub_allocation_form_data["rw_users"] = self.__get_sub_allocation_rw_users(
            users, parent_allocation
        )
        sub_allocation_form_data["ro_users"] = self.__get_sub_allocation_ro_users(users)

        return sub_allocation_form_data

    def __get_sub_allocation_rw_users(
        self, users: dict, parent_allocation: Allocation
    ) -> None:
        rw_users = users.get("rw_users")
        if rw_users is None or rw_users == []:
            rw_allocation = Allocation.objects.get(
                allocationattribute__allocation_attribute_type__name="storage_allocation_pk",
                allocationattribute__value=parent_allocation.id,
                resources__name="rw",
            )
            rw_users = rw_allocation.allocationuser_set.filter(
                status__name="Active"
            ).values_list("user__username", flat=True)

        return rw_users

    def __get_sub_allocation_ro_users(self, users: dict) -> None:
        ro_users = users.get("ro_users")
        if ro_users is None:
            ro_users = []
        return ro_users
