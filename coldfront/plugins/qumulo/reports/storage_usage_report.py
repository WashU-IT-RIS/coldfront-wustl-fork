from coldfront.plugins.qumulo.services.itsm.itsm_client_handler import ItsmClientHandler
from coldfront.plugins.qumulo.validators import is_float
from coldfront.core.allocation.models import Allocation, AllocationLinkage, AllocationAttributeUsage
from datetime import datetime, date, time
import re

class StorageUsageReport:
    def __init__(self, usage_date=datetime.combine(date.today(), time.min)):
       self.usage_date = usage_date

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
        for key in keys:
            col_title[key] = re.sub(r" Kb$", " (KB)", re.sub(r"^Pi$", "PI", key.replace("_", " ").title()))
            # Check if column is float by checking all values
            is_float_col[key] = all(is_float(entry[key]) for entry in usages)
            max_val_len = max(len(f"{float(entry[key]):,.0f}") if is_float_col[key] else len(str(entry[key])) for entry in usages)
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
                    val_str = f"{float(val):,.0f}".rjust(max_col_width[key])
                else:
                    val_str = str(val).ljust(max_col_width[key])
                row.append(val_str)
            rows.append(" | ".join(row))

        report = '\n'.join([header, separator] + rows)
        return report

    def get_departments_by_school(self, unit='ALL') -> list:
        itsm_client = ItsmClientHandler('department')
        uri_filters = self._format_filter_for_dept_by_unit(unit)
        departments = itsm_client.get_data('number', uri_filters)
        dept_numbers = [dept['number'] for dept in departments]
        return dept_numbers

    def _format_filter_for_dept_by_unit(self, unit: str) -> str:
        if unit == 'ALL':
            return f'{{{self._filter_for_valid_dept_number()}}}'
        else:
            return f'{{"unit":"{unit}",{self._filter_for_valid_dept_number()}}}'

    def _filter_for_valid_dept_number(self) -> str:
        return '"number":{"operator":"~*","value":["CH|AU"]}'

    def get_allocations_by_school(self, unit='ALL') -> list:
        allocations = Allocation.objects.filter(
            allocationattribute__allocation_attribute_type__name = 'department_number',
            allocationattribute__value__in = self.get_departments_by_school(unit),
            status__name = 'Active'
        ).exclude(
            id__in = self._get_suballocation_ids()
        ).distinct()
        return allocations

    def _get_suballocation_ids(self) -> list:
        suballoc_ids = list()
        for linkage in AllocationLinkage.objects.all():
            for child in linkage.children.all():
                suballoc_ids.append(child.pk)
        return suballoc_ids

    def get_usages_by_pi_for_school(self, unit='ALL') -> list:
        pi_usages = list()
        allocations = self.get_allocations_by_school(unit)
        for allocation in allocations:
            pi = allocation.project.pi.username
            usage = allocation.get_usage_kb_by_date(self.usage_date)
            if any(entry['pi'] == pi for entry in pi_usages):
                for entry in pi_usages:
                    if entry['pi'] == pi:
                        entry['usage_kb'] = str(float(entry['usage_kb']) + usage)
                        entry['filesystem_path'] += f", {allocation.get_attribute('storage_filesystem_path')}"
            else:
                usage_entry = dict()
                usage_entry['pi'] = pi
                usage_entry['usage_kb'] = str(usage)
                usage_entry['filesystem_path'] = allocation.get_attribute('storage_filesystem_path')
                pi_usages.append(usage_entry)

        sorted_usages_by_pi = sorted(pi_usages, key=lambda x: x['pi'])
        return sorted_usages_by_pi

    def _find_max_length_of_key(self, usage_list: list, key: str) -> int:
        return max(len(entry[key]) for entry in usage_list) if usage_list else 0

    def generate_report_for_school(self, unit='ALL') -> str:
        usages = self.get_usages_by_pi_for_school(unit)
        return self._format_usage_report(usages)

if __name__ == "__main__":
    report_generator = StorageUsageReport()
    school = "Engineering"
    unit = "ENG"
    report = report_generator.generate_report_for_school(unit)
    print(f"Storage Usage Report for {school} on {report_generator.usage_date}:\n")
    print(report)