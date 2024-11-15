import coldfront.plugins.qumulo.services.itsm.fields.transformers
import coldfront.plugins.qumulo.services.itsm.fields.validators

from coldfront.plugins.qumulo.services.itsm.itsm_client import ItsmClient

from coldfront.plugins.qumulo.services.itsm.fields.itsm_to_coldfront_fields_factory import (
    ItsmToColdfrontFieldsFactory,
)


class MigrateToColdfront:

    def __execute(self, fileset_key, itsm_result):
        self.__validate_result_set(fileset_key, itsm_result)
        itsm_allocation = itsm_result[0]
        fields = ItsmToColdfrontFieldsFactory.get_fields(itsm_allocation)
        # for testing
        for field in fields:
            for attribute in field.attributes:
                value = attribute["value"]
                if isinstance(value, dict):
                    transforms = value["transforms"]
                    to_be_validated = field.value
                    if transforms is not None:
                        transforms_function = getattr(
                            coldfront.plugins.qumulo.services.itsm.fields.transformers,
                            transforms,
                        )
                        to_be_validated = transforms_function(field.value)

                    for validator, conditions in value["validates"].items():
                        validator_function = getattr(
                            coldfront.plugins.qumulo.services.itsm.fields.validators,
                            validator,
                        )
                        valid = validator_function(to_be_validated, conditions)

        # TODO create records in coldfront

    def find_by_fileset_alias(self, fileset_alias):
        itsm_result = self.__get_itsm_allocation_by_fileset_alias(fileset_alias)
        self.__execute(fileset_alias, itsm_result)

    def find_by_fileset_name(self, fileset_name):
        itsm_result = self.__get_itsm_allocation_by_fileset_name(fileset_name)
        self.__execute(fileset_name, itsm_result)

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
