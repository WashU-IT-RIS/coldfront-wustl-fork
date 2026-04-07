from datetime import date, datetime
from coldfront.plugins.integratedbilling.constants import ServiceTiers, QUERY_ATTRIBUTE
from coldfront.plugins.qumulo.services.itsm.itsm_client_handler import ItsmClientHandler
from coldfront.plugins.qumulo.reports.storage_usage_report import (
    StorageUsageReport as ColdFrontStorageUsageReport,
)

USAGE_REPORT_HEADER_MAPPING = {
    "fiscal_year": "Fiscal Year",
    "usage_month": "Date",
    "service": "Service",
    "unit": "School",
    "name": "Department",
    "pi": "Sponsor",
    "service_rate_category": "Tier",
    "usage_unit": "Unit",
    "usage": "Usage",
}


class ItsmServiceUsage:

    def __init__(
        self, usage_date: date, tier: ServiceTiers = ServiceTiers.Active
    ) -> None:
        self.usage_date = usage_date
        self.tier = tier
        self.itsm_client = ItsmClientHandler()
        self.itsm_attribute = {
            key: value["itsm"] for key, value in QUERY_ATTRIBUTE.items()
        }

    def get_data(self) -> list[dict[str, str]]:
        filters = self.__get_filters()
        attributes = ",".join(self.itsm_attribute.values())
        return self.itsm_client.get_data(attributes, filters)

    # Private methods
    def __get_filters(self) -> str:
        usage_date_key = self.itsm_attribute["usage_date"]
        service_key = self.itsm_attribute["service"]
        usage_date_str = self.usage_date.strftime("%Y-%m-%d")
        return f'{{"{usage_date_key}":"{usage_date_str}","{service_key}":{self.tier.value}}}'

    def normalized_to_coldfront_report(
        self, raw_report: list[dict[str, str]]
    ) -> list[dict[str, str]]:
        key_mapping = {
            attribute["itsm"]: attribute["coldfront"]
            for attribute in QUERY_ATTRIBUTE.values()
        }
        normalized_report = list()
        for entry in raw_report:
            normalized_entry = dict()
            for old_key, value in entry.items():
                if old_key == self.itsm_attribute["usage_date"]:
                    value = datetime.fromisoformat(
                        value.replace("Z", "+00:00")
                    ).strftime("%Y-%m-%d")
                if old_key == self.itsm_attribute["usage"]:
                    value = int(value.replace("KB", ""))
                if key_mapping.get(old_key):
                    normalized_entry[key_mapping[old_key]] = value
            normalized_report.append(normalized_entry)

        return normalized_report


class ColdfrontServiceUsage:

    def __init__(
        self, usage_date: date, tier: ServiceTiers = ServiceTiers.Active
    ) -> None:
        self.usage_date = usage_date
        self.tier = tier
        self.coldfront_attribute = {
            key: value["coldfront"] for key, value in QUERY_ATTRIBUTE.items()
        }

    def get_data(self) -> list[dict[str, str]]:
        usage_date_str = self.usage_date.strftime("%Y-%m-%d")
        coldfront_usage_report = ColdFrontStorageUsageReport(usage_date=usage_date_str)
        allocations = coldfront_usage_report.get_allocations_by_school()
        s23_usages = list()
        department_key = self.coldfront_attribute["dept_number"]
        service_rate_category_key = self.coldfront_attribute["service_rate_category"]
        usage_key = self.coldfront_attribute["usage"]
        for allocation in allocations:
            entry = dict()
            entry[self.coldfront_attribute["usage_date"]] = usage_date_str
            entry[self.coldfront_attribute["service"]] = self.tier.value
            entry[department_key] = allocation.get_attribute(department_key)
            entry[self.coldfront_attribute["pi"]] = allocation.project.pi.username
            entry[service_rate_category_key] = allocation.get_attribute(
                service_rate_category_key
            )
            entry[usage_key] = allocation.get_usage_kb_by_date(usage_date_str)
            if entry[usage_key] is not None:
                entry[usage_key] = int(entry[usage_key])
                s23_usages.append(entry)

        return s23_usages


class ItsmDepartmentClient:

    def __init__(self) -> None:
        self.itsm_client = ItsmClientHandler("/v2/rest/attr/info/department")
        self.attributes = ["number", "unit", "name"]

    def get_dictionary_by_number(self) -> dict[str, dict[str, str]]:
        uri_filters = self.__format_filter_for_dept()
        departments = self.itsm_client.get_data(",".join(self.attributes), uri_filters)
        return {dept["number"]: dept for dept in departments}

    def __format_filter_for_dept(self) -> str:
        # Only include department numbers starting with CH or AU
        # ~* is case-insensitive regex match
        return f'{{"number":{{"operator":"~*","value":["^CH|^AU"]}}}}'


class StorageUsageReport:

    def __init__(
        self, usage_date: date, tier: ServiceTiers = ServiceTiers.Active
    ) -> None:
        self.usage_date = usage_date
        self.tier = tier
        self.coldfront_attribute = {
            key: value["coldfront"] for key, value in QUERY_ATTRIBUTE.items()
        }

    def generate_report(self) -> str:
        itsm_service_usage = ItsmServiceUsage(self.usage_date, self.tier)
        storage1_usage_data = itsm_service_usage.get_data()
        storage1_usage = itsm_service_usage.normalized_to_coldfront_report(
            storage1_usage_data
        )
        storage23_usage = ColdfrontServiceUsage(self.usage_date, self.tier).get_data()
        storage_usage = storage1_usage + storage23_usage
        sort_group_keys = [
            self.coldfront_attribute["usage_date"],
            self.coldfront_attribute["service"],
            self.coldfront_attribute["dept_number"],
            self.coldfront_attribute["pi"],
            self.coldfront_attribute["service_rate_category"],
        ]
        sorted_storage_usage = self.__sort_usage_data(storage_usage, sort_group_keys)
        grouped_storage_usage = self.__group_usage_data(
            sorted_storage_usage, sort_group_keys
        )
        dept_dictionary = ItsmDepartmentClient().get_dictionary_by_number()
        storage_usage_with_dept_info = self.__append_dept_unit_name_to_usage_data(
            grouped_storage_usage, dept_dictionary
        )

        return self.__format_usage_report(storage_usage_with_dept_info)

    def __sort_usage_data(
        self, usage_data: list[dict[str, str]], sort_keys: list[str]
    ) -> list[dict[str, str]]:
        sorted_usage = sorted(
            usage_data,
            key=lambda x: tuple(x[key] for key in sort_keys),
        )
        return sorted_usage

    def __group_usage_data(
        self, usage_data: list[dict[str, str]], key_attributes: list[str]
    ) -> list[dict[str, str]]:
        grouped_usage = dict()
        for entry in usage_data:
            key = tuple(entry[attr] for attr in key_attributes)
            if key not in grouped_usage:
                grouped_usage[key] = entry
            else:
                grouped_usage[key][self.coldfront_attribute["usage"]] += entry[
                    self.coldfront_attribute["usage"]
                ]
        return list(grouped_usage.values())

    def __append_dept_unit_name_to_usage_data(
        self,
        usage_data: list[dict[str, str]],
        dept_dictionary: dict[str, dict[str, str]],
    ) -> list[dict[str, str]]:
        for entry in usage_data:
            dept_number = entry[self.coldfront_attribute["dept_number"]]
            entry["unit"] = dept_dictionary.get(dept_number, {}).get("unit", "Unknown")
            entry["name"] = dept_dictionary.get(dept_number, {}).get("name", "Unknown")

        return self.__sort_usage_data(
            usage_data,
            [
                self.coldfront_attribute["usage_date"],
                self.coldfront_attribute["service"],
                "unit",
                "name",
                self.coldfront_attribute["pi"],
            ],
        )

    def __format_usage_report(self, usage_data: list[dict[str, str]]) -> str:
        report_header = [
            USAGE_REPORT_HEADER_MAPPING[key] for key in USAGE_REPORT_HEADER_MAPPING
        ]
        formatted_report = ",".join(report_header) + "\n"
        fiscal_year = (
            self.usage_date.year
            if self.usage_date.month < 7
            else self.usage_date.year + 1
        )
        fiscal_year = f"FY{str(fiscal_year)[-2:]}"
        usage_month = self.usage_date.strftime("%Y-%m")
        service = f"Storage {self.tier.name}"
        for entry in usage_data:
            formatted_entry = ",".join(
                [
                    fiscal_year,
                    usage_month,
                    service,
                    entry.get("unit", "Unknown"),
                    entry.get("name", "Unknown"),
                    entry.get(self.coldfront_attribute["pi"], "Unknown"),
                    entry.get(
                        self.coldfront_attribute["service_rate_category"], "Unknown"
                    ),
                    "KB",
                    str(entry.get(self.coldfront_attribute["usage"], 0)),
                ]
            )
            formatted_report += formatted_entry + "\n"
        return formatted_report
