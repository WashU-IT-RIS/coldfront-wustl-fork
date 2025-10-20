from ast import Constant
from datetime import date, datetime
from time import sleep
from typing import Union
from coldfront.core.service_rate_category.models import Service
from coldfront.plugins.integratedbilling.billing_itsm_client import BillingItsmClient
from coldfront.plugins.integratedbilling.constants import BillingDataSources
from coldfront.core.billing.models import AllocationUsage


class ItsmUsageIngestor:

    def __init__(self, client: BillingItsmClient):
        self.client = client
        self.service = Service.objects.get(name="Storage1")
        self.source = BillingDataSources.ITSM.value

    def process_usages(self) -> bool:
        usages = self.__ingest_usages()
        if usages is None:
            # consider throwing an exception here
            return False

        if usages == []:
            # No usages to process since the usages ITSM have not been processed
            return False

        valid_usages = [
            usage
            for usage in usages
            if usage.get("amount")
            and self.__convert_to_amount_usage_to_tb(usage.get("amount")) is not None
        ]
        created_usages = self.__create_allocation_usage_records(valid_usages)

        if not created_usages:
            return False

        return True

    # Private methods
    def __ingest_usages(self) -> list[dict]:
        # try accessing API 3 times before failing
        for _ in range(3):
            try:
                data = self.client.get_billing_usages()
                if data:
                    return data
                sleep(5)
            except Exception as e:
                continue
        return None

    def __convert_to_amount_usage_to_tb(
        self, amount_kb_with_unit: str
    ) -> Union[float, None]:
        try:
            amount_kb = int(amount_kb_with_unit.replace("KB", "").replace(",", ""))
            amount_tb = float(amount_kb) / 1_000_000_000  # 1024**3 perhaps
            return round(amount_tb, 6)
        except (TypeError, ValueError):
            return None

    def __get_billing_contact(self, usage: dict) -> str:
        return usage.get("billing_contact") or usage.get("sponsor")

    def __create_allocation_usage_records(
        self, valid_usages: list[dict]
    ) -> list[AllocationUsage]:
        usage_records = []
        for usage in valid_usages:
            amount_tb = self.__convert_to_amount_usage_to_tb(usage.get("amount"))
            billing_contact = self.__get_billing_contact(usage)
            record = AllocationUsage(
                external_key=usage.get("id"),
                source=self.source,
                sponsor_pi=usage.get("sponsor"),
                billing_contact=billing_contact,
                fileset_name=usage.get("fileset_name"),
                service_rate_category=usage.get("service_rate_category"),
                usage_tb=amount_tb,
                funding_number=usage.get("funding_number") or "NOT PROVIDED",
                exempt=usage.get("exempt"),
                subsidized=usage.get("subsidized"),
                is_condo_group=usage.get("is_condo_group"),
                parent_id_key=usage.get("parent_id"),
                quota=usage.get("quota"),
                billing_cycle=usage.get("billing_cycle"),
                usage_date=datetime.strptime(
                    usage.get("provision_usage_creation_date"), "%Y-%m-%dT%H:%M:%S.%fZ"
                ).date(),
                storage_cluster=self.service.name,
            )
            usage_records.append(record)

        if not usage_records:
            return []

        created_usages = AllocationUsage.objects.bulk_create(usage_records)
        return created_usages
