from coldfront.plugins.qumulo.services.itsm.itsm_client import ItsmClient
from coldfront.plugins.qumulo.services.itsm.fields.itsm_to_coldfront_factory import (
    coldfront_field_map,
    validator_map,
    Field,
)

class MigrateToColdfront:

    def find_by_fileset_name(self, fileset_name):
        itsm_result = self.get_itsm_allocation(fileset_name)

        self.validate_result_set(itsm_result)

        itsm_allocation = itsm_result[0]

        fields = self.create_fields(itsm_allocation)

        valid = self.validate_coldfront_allocation_preprosesing(fields)

        if not valid:
            raise Exception(f"ITSM allocation rejected. Fileset_name: {fileset_name} ")

        self.create_coldfront_allocation(fields)

    def get_itsm_allocation(self, fileset_name):
        itsm_client = ItsmClient()
        itsm_allocation = itsm_client.get_fs1_allocation(fileset_name)
        return itsm_allocation

    def get_mapper(self):
        return coldfront_field_map

    def validate_result_set(self, fileset_name, itsm_result) -> bool:
        how_many = len(itsm_result)
        # ITSM does not return a respond code of 404 when the service provision record is not found.
        # Instead, it return an empty array.
        if how_many == 0:
            raise Exception(f"ITSM allocation was not found for fileset_name \"{fileset_name}\"")

        if how_many > 1:
            raise Exception(f"Multiple ({how_many} total) ITSM allocations were found for {fileset_name}")

        return True


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



"""        form_data = {
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
        #allocation = create_allocation(
        #    project=self.project, user=self.user, form_data=form_data
        #)


def main() -> None:
    MigrateToColdfront("jin810_active")
    MigrateToColdfront("non_found")
    MigrateToColdfront()


if __name__ == "__main__":
    main()
"""
from coldfront.plugins.qumulo.services.itsm.migrate_to_coldfront import MigrateToColdfront
jin = MigrateToColdfront("jin810_active")
jin.execute()

ina = MigrateToColdfront("ina.amarillo_active")
ina.execute()

not_found = MigrateToColdfront("non_found")
not_found.execute()
"""