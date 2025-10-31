from coldfront.plugins.qumulo.services.itsm.fields.itsm_to_coldfront_fields_factory import (
    itsm_attributes,
)
from coldfront.plugins.qumulo.services.itsm.itsm_client_handler import ItsmClientHandler


# this should be named MigrationItsmClient but that would require a lot of renaming
# so leaving as is for now
class ItsmClient:
    def __init__(self):
        self.itsm_client_handler = ItsmClientHandler()

    def get_fs1_allocation_by_fileset_name(self, fileset_name) -> str:
        return self._get_fs1_allocation_by("fileset_name", fileset_name)

    def get_fs1_allocation_by_fileset_alias(self, fileset_alias) -> str:
        return self._get_fs1_allocation_by("fileset_alias", fileset_alias)

    def get_fs1_allocation_by_storage_provision_name(
        self, storage_provision_name
    ) -> str:
        return self._get_fs1_allocation_by("name", storage_provision_name)

    # Private methods
    def _get_fs1_allocation_by(self, fileset_key, fileset_value) -> str:
        attributes = self._get_attributes()
        filters = self._get_filters(fileset_key, fileset_value)
        return self.itsm_client_handler.get_data(attributes, filters)

    def _get_attributes(self) -> str:
        return ",".join(itsm_attributes)

    def _get_filters(self, fileset_key, fileset_value) -> str:
        itsm_active_allocation_service_id = 1
        status = "active"
        return f'{{"{fileset_key}":"{fileset_value}","status":"{status}","service_id":{itsm_active_allocation_service_id}}}'
