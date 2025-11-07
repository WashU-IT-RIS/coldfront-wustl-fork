from datetime import datetime, timezone
from time import sleep
from typing import Union

from coldfront.plugins.integratedbilling.billing_itsm_client import BillingItsmClient
from coldfront.plugins.integratedbilling.constants import (
    BillingDataSources,
    StorageClusters,
    ServiceTiers,
)
from coldfront.core.billing.models import AllocationUsage


class ItsmUsageIngestor:

    def __init__(self, client: BillingItsmClient):
        self.client = client
        self.storage_cluster = StorageClusters.STORAGE1.value
        self.source = BillingDataSources.ITSM.value

    def process_usages(self) -> bool:
        usages = self.__ingest_usages()
        if usages is None:
            print("Failed to fetch ITSM usage data after multiple attempts.")
            return False

        valid_usages = [
            usage
            for usage in usages
            if usage.get("amount")
            and self.__convert_to_amount_usage_to_tb(usage.get("amount")) is not None
        ]
        created_usages = self.__create_allocation_usage_records(valid_usages)

        if not created_usages:
            print(
                "No ITSM allocation usage records were created since the data fetch was empty."
            )
        return True

    # Private methods
    def __ingest_usages(self) -> Union[list[dict], None]:
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
            amount_tb = float(amount_kb) / 1_073_741_824  # 2**30 or 1024**3
            return round(amount_tb, 6)
        except (TypeError, ValueError):
            return None

    def __get_billing_contact(self, usage: dict) -> str:
        return usage.get("billing_contact") or usage.get("sponsor")

    def __create_allocation_usage_records(
        self, valid_usages: list[dict]
    ) -> list[AllocationUsage]:
        saved_usages = []
        for usage in valid_usages:
            amount_tb = self.__convert_to_amount_usage_to_tb(usage.get("amount"))
            billing_contact = self.__get_billing_contact(usage)
            record = AllocationUsage.objects.update_or_create(
                tier=self.__get_tier(usage),
                fileset_name=usage.get("fileset_name"),
                source=self.source,
                usage_date=datetime.strptime(
                    usage.get("provision_usage_creation_date"), "%Y-%m-%dT%H:%M:%S.%fZ"
                )
                .replace(
                    hour=18, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
                )
                .date(),
                defaults={
                    "external_key": usage.get("id"),
                    "sponsor_pi": usage.get("sponsor"),
                    "billing_contact": billing_contact,
                    "fileset_name": usage.get("fileset_name"),
                    "service_rate_category": usage.get("service_rate_category"),
                    "usage_tb": amount_tb,
                    "funding_number": self.__get_funding_number(usage),
                    "exempt": usage.get("exempt"),
                    "subsidized": self.__get_subsidized(usage),
                    "is_condo_group": usage.get("is_condo_group"),
                    "parent_id_key": usage.get("parent_id"),
                    "quota": usage.get("quota"),
                    "billing_cycle": usage.get("billing_cycle"),
                    "storage_cluster": self.storage_cluster,
                },
            )
            saved_usages.append(record)

        return saved_usages

    # TODO: should we ask for funding number if not present from Research Facilitators?
    def __get_funding_number(self, usage: dict) -> str:
        return usage.get("funding_number") or ""

    def __get_tier(self, usage: dict) -> str:
        if service_id := usage.get("service_id"):
            if int(service_id) == 2:
                return ServiceTiers.Archive.name
            if int(service_id) == 1:
                return ServiceTiers.Active.name
        return ServiceTiers.Active.name

    def __get_subsidized(self, usage: dict) -> bool:
        service_id = usage.get("service_id")
        # Treat Archive service as non-subsidized since ITSM (wrongly) sets all archive to subsidized
        if int(service_id) == 2:
            return False
        return usage.get("subsidized", False)
