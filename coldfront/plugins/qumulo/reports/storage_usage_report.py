from coldfront.plugins.qumulo.services.itsm.itsm_client_handler import ItsmClientHandler
from coldfront.plugins.qumulo.validators import is_float
from coldfront.core.allocation.models import (
    Allocation,
    AllocationLinkage,
    AllocationQuerySet,
)
from coldfront.core.project.models import Project
from coldfront.core.constants import CONDO_PROJECT_QUOTA
from datetime import datetime, date, time
from typing import Any, Optional
import re


class StorageUsageReport:
    def __init__(self, usage_date=None):
        if usage_date is None:
            usage_date = datetime.combine(date.today(), time.min)
        self.usage_date = usage_date

    def _convert_usage_units(self, usages: list) -> list:
        """
        Replace the usage_kb column with usage_gb and usage_tb columns,
        keeping the original column position.
        """
        converted = []
        for entry in usages:
            new_entry = {}
            for key, val in entry.items():
                if key == "usage_kb":
                    usage_kb = float(val)
                    new_entry["usage_gb"] = str(usage_kb / 1024**2)
                    new_entry["usage_tb"] = str(usage_kb / 1024**3)
                else:
                    new_entry[key] = val
            converted.append(new_entry)
        return converted

    def _format_usage_report(self, usages: list) -> str:
        """
        Format the list of usages as a table-like report string.
        If the column is float, align its values to the right, else, align to the left.
        """
        if not usages:
            return "No usage data available."

        # Determine column names and widths
        keys = list(usages[-1].keys()) if usages else []
        col_title = {}
        max_col_width = {}
        is_float_col = {}
        decimals = {}
        for key in keys:
            # GB/TB values are often small, so show them with 2 decimal places
            decimals[key] = 2 if key in ("usage_gb", "usage_tb") else 0
            col_title[key] = re.sub(
                r" (Kb|Gb|Tb)$",
                lambda m: f" ({m.group(1).upper()})",
                re.sub(r"^Pi$", "PI", key.replace("_", " ").title()),
            )
            # Check if column is float by checking all values
            is_float_col[key] = all(is_float(entry[key]) for entry in usages)
            max_val_len = max(
                (
                    len(f"{float(entry[key]):,.{decimals[key]}f}")
                    if is_float_col[key]
                    else len(str(entry[key]))
                )
                for entry in usages
            )
            max_col_width[key] = max(len(col_title[key]), max_val_len)

        # Header
        header = " | ".join(col_title[key].center(max_col_width[key]) for key in keys)
        separator = "-+-".join("-" * max_col_width[key] for key in keys)

        # Rows
        rows = []
        for entry in usages:
            row = []
            for key in keys:
                val = entry[key]
                if is_float_col[key]:
                    val_str = f"{float(val):,.{decimals[key]}f}".rjust(
                        max_col_width[key]
                    )
                else:
                    val_str = str(val).ljust(max_col_width[key])
                row.append(val_str)
            rows.append(" | ".join(row))

        report = "\n".join([header, separator] + rows)
        return report

    def get_departments_by_school(self, school_unit="ALL") -> list:
        itsm_client = ItsmClientHandler("/v2/rest/attr/info/department")
        uri_filters = self._format_filter_for_dept_by_unit(school_unit)
        departments = itsm_client.get_data("number", uri_filters)
        dept_numbers = [dept["number"] for dept in departments]
        return dept_numbers

    def _format_filter_for_dept_by_unit(self, unit: str) -> str:
        if unit == "ALL":
            return f"{{{self._filter_for_valid_dept_number()}}}"
        else:
            return f'{{"unit":"{unit}",{self._filter_for_valid_dept_number()}}}'

    def _filter_for_valid_dept_number(self) -> str:
        # Only include department numbers starting with CH or AU
        # ~* is case-insensitive regex match
        return '"number":{"operator":"~*","value":["^CH|^AU"]}'

    def get_allocations(self) -> AllocationQuerySet:
        return self.get_allocations_by_school("ALL")

    def get_allocations_by_school(self, school_unit="ALL") -> AllocationQuerySet:
        allocations = Allocation.objects.parents().filter(
            allocationattribute__allocation_attribute_type__name="department_number",
            allocationattribute__value__in=self.get_departments_by_school(school_unit),
            status__name="Active",
        )
        return allocations

    def get_allocations_by_project(self, project: str) -> AllocationQuerySet:
        project_object = Project.objects.get(title=project)
        project_id = project_object.pk
        return Allocation.objects.parents().filter(
            project__pk=project_id,
            status__name="Active",
        )

    def _get_suballocation_ids(self) -> list[int]:
        suballoc_ids = list()
        for linkage in AllocationLinkage.objects.all():
            for child in linkage.children.all():
                suballoc_ids.append(child.pk)
        return suballoc_ids

    def get_usages_by_pi_for_school(self, school_unit="ALL") -> list[dict[str, Any]]:
        pi_usages = list()
        allocations = self.get_allocations_by_school(school_unit)
        for allocation in allocations:
            pi = allocation.project.pi.username
            usage = allocation.get_usage_kb_by_date(self.usage_date)
            if usage is None:
                continue
            if any(entry["pi"] == pi for entry in pi_usages):
                for entry in pi_usages:
                    if entry["pi"] == pi:
                        entry["usage_kb"] = str(float(entry["usage_kb"]) + usage)
                        entry[
                            "filesystem_path"
                        ] += f", {allocation.get_attribute('storage_filesystem_path')}"
            else:
                usage_entry = dict()
                usage_entry["pi"] = pi
                usage_entry["usage_kb"] = str(usage)
                usage_entry["filesystem_path"] = allocation.get_attribute(
                    "storage_filesystem_path"
                )
                pi_usages.append(usage_entry)

        if not pi_usages:
            return []
        sorted_usages_by_pi = sorted(pi_usages, key=lambda x: x["pi"])
        return sorted_usages_by_pi

    def get_usages_by_pi_for_project(self, project: str) -> list[dict[str, Any]]:
            pi_usages = list()
            allocations = self.get_allocations_by_project(project)
            for allocation in allocations:
                pi = allocation.project.pi.username
                usage = allocation.get_usage_kb_by_date(self.usage_date)
                if usage is None:
                    continue
                if any(entry["pi"] == pi for entry in pi_usages):
                    for entry in pi_usages:
                        if entry["pi"] == pi:
                            entry["usage_kb"] = str(float(entry["usage_kb"]) + usage)
                            entry[
                                "filesystem_path"
                            ] += f", {allocation.get_attribute('storage_filesystem_path')}"
                else:
                    usage_entry = dict()
                    usage_entry["pi"] = pi
                    usage_entry["usage_kb"] = str(usage)
                    usage_entry["filesystem_path"] = allocation.get_attribute(
                        "storage_filesystem_path"
                    )
                    pi_usages.append(usage_entry)
    
            if not pi_usages:
                return []
            sorted_usages_by_pi = sorted(pi_usages, key=lambda x: x["pi"])
            return sorted_usages_by_pi
    

    def _find_max_length_of_key(self, usage_list: list, key: str) -> int:
        return max(len(entry[key]) for entry in usage_list) if usage_list else 0

    def generate_report_for_school(self, school_unit="ALL") -> str:
        usages = self.get_usages_by_pi_for_school(school_unit)
        return self._format_usage_report(usages)

    def get_project_summary(self, project: str) -> dict[str, float]:
        """
        Summarize the condo's quota and usage, all values in TB.
        storage_quota is stored in TB; usage is converted from KB (1 TB = 1024**3 KB).
        """
        allocated_tb = 0.0
        used_tb = 0.0
        for allocation in self.get_allocations_by_project(project):
            quota = allocation.get_attribute("storage_quota")
            if quota is not None:
                allocated_tb += float(quota)
            usage_kb = allocation.get_usage_kb_by_date(self.usage_date)
            if usage_kb is not None:
                used_tb += usage_kb / 1024**3

        return {
            "total_quota_tb": float(CONDO_PROJECT_QUOTA),
            "allocated_tb": allocated_tb,
            "unallocated_tb": CONDO_PROJECT_QUOTA - allocated_tb,
            "used_tb": used_tb,
        }

    def _format_tb(self, value: float) -> str:
        return f"{value:,.3f} TB"

    def _format_percent(self, part: float, whole: float) -> str:
        return f"{part / whole * 100:.0f}%" if whole else "N/A"

    def _format_project_summary(self, summary: dict[str, float]) -> str:
        total = summary["total_quota_tb"]
        allocated = summary["allocated_tb"]
        return "\n".join(
            [
                f"Total condo quota: {self._format_tb(total)}",
                f"Allocated to PIs: {self._format_tb(allocated)}"
                f" ({self._format_percent(allocated, total)})",
                f"Unallocated: {self._format_tb(summary['unallocated_tb'])}",
                f"Used: {self._format_tb(summary['used_tb'])}"
                f" ({self._format_percent(summary['used_tb'], allocated)} of allocated)",
            ]
        )

    def generate_report_for_project(self, project: Any) -> str:
            summary = self._format_project_summary(self.get_project_summary(project))
            usages = self.get_usages_by_pi_for_project(project)
            table = self._format_usage_report(self._convert_usage_units(usages))
            return f"{summary}\n\n{table}"
