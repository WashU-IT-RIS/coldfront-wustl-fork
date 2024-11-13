from coldfront.plugins.qumulo.services.itsm.itsm_client import ItsmClient
from coldfront.plugins.qumulo.services.itsm.fields.itsm_to_coldfront_factory import (
    ItsmToColdfrontFactory,
)


class MigrateToColdfront:

    def find_by_fileset_alias(self, fileset_alias):
        itsm_result = self.__get_itsm_allocation_by_fileset_alias(fileset_alias)
        self.__execute(fileset_alias, itsm_result)

    def find_by_fileset_name(self, fileset_name):
        itsm_result = self.__get_itsm_allocation_by_fileset_name(fileset_name)
        self.__execute(fileset_name, itsm_result)

    def __execute(self, fileset_key, itsm_result):
        self.__validate_result_set(fileset_key, itsm_result)
        itsm_allocation = itsm_result[0]
        fields = ItsmToColdfrontFactory.get_fields(itsm_allocation)
        # for testing
        for field in fields:
            print(field.value)
            print(field.entity)
            print(field.attributes)
        print("-------------------")
        # TODO validate each field value
        # TODO create records in coldfront

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


"""
    def create_fields(self, itsm_allocation)-> dict:
        mapper = self.get_mapper()
        fields = {}

        for itsm_name, coldfront_name in mapper.items():
            value = itsm_allocation.get(itsm_name)
            coldfront_field = Field(coldfront_name, itsm_name, value)

            validator = validator_map.get(itsm_name)
            if validator is not None:
                coldfront_field.set_validator(validator)

            fields[itsm_name] = coldfront_field
        return fields

    # users AllocationForm(data=data, user_id=self.user.id).is_valid() to validate the form
    def validate_coldfront_allocation_preprosesing(self, fields)-> bool:
        valid = True
        for field in fields.values():
            valid = valid and field.is_valid()
        return valid

    def create_coldfront_allocation(self, fields):
        mapper = self.get_mapper()

        for index, (key, field) in enumerate(fields.items()):
            if field.get_name_coldfront() is None:
                continue

        try:
            print(key, field.get_value())
        except Exception as validation_exception:
            print(repr(validation_exception))

        form_data = {}
        for index, (key, field) in enumerate(fields.items()):
            try:
                form_data[key] = field.get_value()
            except Exception as validation_exception:
                print(repr(validation_exception))

        print(form_data)

        form_data = {
            "storage_filesystem_path": path.rstrip("/"),
            "storage_export_path": path.rstrip("/"),
            "storage_name": self.fileset_name,
            "storage_quota": fields.get("quota").get_value(),
            "protocols": ["nfs"],
            "rw_users": self.get_users_rw(),
            "ro_users": self.get_users_ro(),
            "storage_ticket": fields.get("quota").get_value(),
            "cost_center": "Uncle Pennybags",
            "department_number": "Time Travel Services",
            "service_rate": "general",
        } """
# allocation = create_allocation(
#    project=self.project, user=self.user, form_data=form_data
# )

"""
from coldfront.plugins.qumulo.services.itsm.migrate_to_coldfront import MigrateToColdfront
migrator = MigrateToColdfront()
migrator.find_by_fileset_name("jin810_active")

not_found = MigrateToColdfront()
migrator.find_by_fileset_name("not_found")

curl -k -s --user "$user:$pass" --cookie-jar /tmp/test-cookie "https://itsm.ris.wustl.edu:8443/v2/rest/attr/info/service_provision?attribute=id,service_id,name,sponsor,department_number,department_name,funding_number,billing_contact,technical_contact,secure,service_desk_ticket_number,audit,creation_timestamp,billing_startdate,status,sponsor_department_number,fileset_name,fileset_alias,exempt,service_rate_category,comment,billing_cycle,subsidized,quota,allow_nonfaculty,acl_group_members,who,parent_id,is_condo_group,sla"
"""
