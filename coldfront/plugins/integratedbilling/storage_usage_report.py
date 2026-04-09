from typing import Any, Optional
from datetime import date, datetime
from coldfront.plugins.integratedbilling.constants import ServiceTiers, QUERY_ATTRIBUTE
from coldfront.plugins.qumulo.services.itsm.itsm_client_handler import ItsmClientHandler
from coldfront.plugins.qumulo.reports.storage_usage_report import (
    StorageUsageReport as ColdFrontStorageUsageReport,
)

CSV_USAGE_REPORT_HEADER_MAPPING = {
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
    """
    Handles ITSM (IT Service Management) service usage data retrieval and normalization for ColdFront integrated billing.

    This class is responsible for:
    - Querying ITSM usage data for a given date and service tier using the ItsmClientHandler.
    - Mapping ITSM attributes to ColdFront report fields.
    - Normalizing raw ITSM report data into the format expected by ColdFront reports.
    """

    def __init__(
        self, usage_date: date, tier: ServiceTiers = ServiceTiers.Active
    ) -> None:
        self.usage_date = usage_date
        self.tier = tier
        self.itsm_client = ItsmClientHandler()
        self.itsm_attribute = {
            key: value["itsm"] for key, value in QUERY_ATTRIBUTE.items()
        }

    def get_data(self) -> list[dict[str, Any]]:
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
        self, raw_report: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
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
    """
    Retrieves and formats ColdFront service usage data for integrated billing reports.

    This class is responsible for:
    - Querying ColdFront allocation and usage data for a given date and service tier.
    - Mapping ColdFront attributes to report fields as defined in QUERY_ATTRIBUTE.
    - Producing usage records in the format expected for integrated billing and reporting.
    """

    def __init__(
        self, usage_date: date, tier: ServiceTiers = ServiceTiers.Active
    ) -> None:
        self.usage_date = usage_date
        self.tier = tier
        self.coldfront_attribute = {
            key: value["coldfront"] for key, value in QUERY_ATTRIBUTE.items()
        }

    def get_data(self) -> list[dict[str, Any]]:
        usage_date_str = self.usage_date.strftime("%Y-%m-%d")
        coldfront_usage_report = ColdFrontStorageUsageReport(usage_date=self.usage_date)
        allocations = coldfront_usage_report.get_allocations()
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
            entry[usage_key] = allocation.get_usage_kb_by_date(self.usage_date)
            if entry[usage_key] is not None:
                entry[usage_key] = int(entry[usage_key])
                s23_usages.append(entry)

        return s23_usages


class ItsmDepartmentClient:
    """
    Client for retrieving department information from the ITSM system.

    This class is responsible for:
    - Querying department data from the ITSM API endpoint.
    - Filtering departments by number prefix (e.g., CH or AU).
    - Returning department data as a dictionary keyed by department number.
    """

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
    """
    Generates a comprehensive storage usage report for integrated billing.

    This class is responsible for:
    - Aggregating and normalizing usage data from ITSM and ColdFront sources for a given date and service tier.
    - Merging, sorting, and grouping usage data by department, PI, and service attributes.
    - Enriching usage data with department information from ITSM.
    - Formatting the final report as a CSV string for export or further processing.
    """

    def __init__(
        self, usage_date: date, tier: ServiceTiers = ServiceTiers.Active
    ) -> None:
        self.usage_date = usage_date
        self.tier = tier
        self.report_attribute = {
            key: value["coldfront"] for key, value in QUERY_ATTRIBUTE.items()
        }
        self.report_attribute |= {"unit": "unit", "name": "name"}

    def generate_report(self, filename: Optional[str] = None) -> str:
        """
        Generate the storage usage report as a CSV string. If filename is provided, write the CSV to that file.
        """
        itsm_service_usage = ItsmServiceUsage(self.usage_date, self.tier)
        storage1_usage_data = itsm_service_usage.get_data()
        storage1_usage = itsm_service_usage.normalized_to_coldfront_report(
            storage1_usage_data
        )
        storage23_usage = ColdfrontServiceUsage(self.usage_date, self.tier).get_data()
        storage_usage = storage1_usage + storage23_usage
        sort_group_keys = [
            self.report_attribute["usage_date"],
            self.report_attribute["service"],
            self.report_attribute["dept_number"],
            self.report_attribute["pi"],
            self.report_attribute["service_rate_category"],
        ]
        sorted_storage_usage = self.__sort_usage_data(storage_usage, sort_group_keys)
        grouped_storage_usage = self.__group_usage_data(
            sorted_storage_usage, sort_group_keys
        )
        dept_dictionary = ItsmDepartmentClient().get_dictionary_by_number()
        storage_usage_with_dept_info = self.__append_dept_unit_name_to_usage_data(
            grouped_storage_usage, dept_dictionary
        )
        csv_output = self.__format_csv_usage_report(storage_usage_with_dept_info)
        if filename is not None:
            # Write the CSV output to the specified file
            self.write_csv_to_tmp(csv_output, filename)
            print(f"Storage usage report written to {filename}")
        return csv_output

    def __sort_usage_data(
        self, usage_data: list[dict[str, Any]], sort_keys: list[str]
    ) -> list[dict[str, Any]]:
        sorted_usage = sorted(
            usage_data,
            key=lambda x: tuple(x[key] for key in sort_keys),
        )
        return sorted_usage

    def __group_usage_data(
        self, usage_data: list[dict[str, Any]], key_attributes: list[str]
    ) -> list[dict[str, Any]]:
        grouped_usage = dict()
        for entry in usage_data:
            key = tuple(entry[attr] for attr in key_attributes)
            if key not in grouped_usage:
                grouped_usage[key] = entry
            else:
                grouped_usage[key][self.report_attribute["usage"]] += entry[
                    self.report_attribute["usage"]
                ]
        return list(grouped_usage.values())

    def __append_dept_unit_name_to_usage_data(
        self,
        usage_data: list[dict[str, Any]],
        dept_dictionary: dict[str, dict[str, str]],
    ) -> list[dict[str, Any]]:
        for entry in usage_data:
            dept_number = entry[self.report_attribute["dept_number"]]
            entry[self.report_attribute["unit"]] = dept_dictionary.get(
                dept_number, {}
            ).get("unit", "Unknown")
            entry[self.report_attribute["name"]] = dept_dictionary.get(
                dept_number, {}
            ).get("name", "Unknown")

        return self.__sort_usage_data(
            usage_data,
            [
                self.report_attribute["usage_date"],
                self.report_attribute["service"],
                self.report_attribute["unit"],
                self.report_attribute["name"],
                self.report_attribute["pi"],
            ],
        )

    def __format_csv_usage_report(self, usage_data: list[dict[str, str]]) -> str:
        csv_row = list()
        report_header = [
            CSV_USAGE_REPORT_HEADER_MAPPING[key]
            for key in CSV_USAGE_REPORT_HEADER_MAPPING
        ]
        csv_row.append(",".join(report_header))
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
                    entry.get(self.report_attribute["unit"], "Unknown"),
                    entry.get(self.report_attribute["name"], "Unknown"),
                    entry.get(self.report_attribute["pi"], "Unknown"),
                    entry.get(
                        self.report_attribute["service_rate_category"], "Unknown"
                    ),
                    "KB",
                    str(entry.get(self.report_attribute["usage"], 0)),
                ]
            )
            csv_row.append(formatted_entry)
        formatted_report = "\n".join(csv_row)
        return formatted_report

    def write_csv_to_tmp(self, csv_rows: str, filename: str = None) -> Optional[str]:
        """
        Write a CSV string to a file in /tmp.
        If filename is None, generate a filename with usage_date and tier.
        Returns the file path. Catches and reports file write errors.
        """
        import os

        try:
            if filename is None:
                tier_name = self.tier.name.lower()
                date_str = self.usage_date.strftime("%Y%m%d")
                filename = f"storage_{tier_name}_usage_{date_str}.csv"
            file_path = os.path.join("/tmp", filename)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(csv_rows)
            return file_path
        except Exception as e:
            print(f"Failed to write CSV to {filename or '/tmp'}: {e}")
            return None
