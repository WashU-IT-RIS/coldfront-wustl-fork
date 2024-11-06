from coldfront.plugins.qumulo.services.itsm.field import Field
from coldfront.plugins.qumulo.services.itsm.validators.allocation_attributes import validate_ticket

import json, re, yaml

field_map = {
    "id": "itsm_id",
    "service_id": None,
    "name": "storage_name",
    "sponsor": None,
    "department_number": "department_number",
    "department_name": None,
    "funding_number": "cost_center",
    "billing_contact": None,
    "technical_contact": None,
    "secure": None,
    "service_desk_ticket_number": "storage_ticket",
    "audit": None,
    "creation_timestamp": None,
    "billing_startdate": None,
    "status": None,
    "sponsor_department_number": None,
    "fileset_name": None,
    "fileset_alias": None,
    "exempt": None,
    "service_rate_category": "service_rate",
    "comment": None,
    "billing_cycle": None,
    "subsidized": None,
    "quota": "storage_quota",
    "allow_nonfaculty": None,
    "acl_group_members": None,
    "who": None,
    "parent_id": None,
    "is_condo_group": None,
    "sla": None,
}

validator_map = {
    "service_desk_ticket_number": validate_ticket,
}

itsm_attributes = field_map.keys()

coldfront_field_map = {
    itsm_name: coldfront_name
    for itsm_name, coldfront_name in field_map.items()
    if coldfront_name is not None
}


def main() -> None:

    fields = {}

    for itsm_name, coldfront_name in coldfront_field_map.items():
        fields[itsm_name] = Field(coldfront_name, itsm_name, "test")
        print(fields[itsm_name])

    for index, (key, field) in enumerate(fields.items()):
        print(index)
        if field.get_name_coldfront() is None:
            continue
        print(key, field)


if __name__ == "__main__":
    main()



"""
from coldfront.plugins.qumulo.services.itsm.migrate_to_coldfront import MigrateToColdfront
jin = MigrateToColdfront("jin810_active")
jin.execute()Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/Users/marshalljansen/Documents/github_projects/coldfront-wustl-fork/coldfront/plugins/qumulo/services/itsm/migrate_to_coldfront.py", line 1, in <module>
    from coldfront.plugins.qumulo.services.itsm.itsm_client import ItsmClient
  File "/Users/marshalljansen/Documents/github_projects/coldfront-wustl-fork/coldfront/plugins/qumulo/services/itsm/itsm_client.py", line 6, in <module>
    from coldfront.plugins.qumulo.services.itsm.allocation_fields_factory import (
  File "/Users/marshalljansen/Documents/github_projects/coldfront-wustl-fork/coldfront/plugins/qumulo/services/itsm/allocation_fields_factory.py", line 3, in <module>
    from coldfront.plugins.qumulo.validators import (
  File "/Users/marshalljansen/Documents/github_projects/coldfront-wustl-fork/coldfront/plugins/qumulo/validators.py", line 7, in <module>
    from coldfront.core.allocation.models import (
  File "/Users/marshalljansen/Documents/github_projects/coldfront-wustl-fork/coldfront/core/allocation/models.py", line 8, in <module>
    from django.contrib.auth.models import User
  File "/Users/marshalljansen/Documents/github_projects/coldfront-wustl-fork/coldfront-venv/lib/python3.9/site-packages/django/contrib/auth/models.py", line 3, in <module>
    from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
  File "/Users/marshalljansen/Documents/github_projects/coldfront-wustl-fork/coldfront-venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py", line 48, in <module>
    class AbstractBaseUser(models.Model):
  File "/Users/marshalljansen/Documents/github_projects/coldfront-wustl-fork/coldfront-venv/lib/python3.9/site-packages/django/db/models/base.py", line 108, in __new__
    app_config = apps.get_containing_app_config(module)
  File "/Users/marshalljansen/Documents/github_projects/coldfront-wustl-fork/coldfront-venv/lib/python3.9/site-packages/django/apps/registry.py", line 253, in get_containing_app_config
    self.check_apps_ready()
  File "/Users/marshalljansen/Documents/github_projects/coldfront-wustl-fork/coldfront-venv/lib/python3.9/site-packages/django/apps/registry.py", line 135, in check_apps_ready
    settings.INSTALLED_APPS
  File "/Users/marshalljansen/Documents/github_projects/coldfront-wustl-fork/coldfront-venv/lib/python3.9/site-packages/django/conf/__init__.py", line 82, in __getattr__
    self._setup(name)
  File "/Users/marshalljansen/Documents/github_projects/coldfront-wustl-fork/coldfront-venv/lib/python3.9/site-packages/django/conf/__init__.py", line 63, in _setup
    raise ImproperlyConfigured(
django.core.exceptions.ImproperlyConfigured: Requested setting INSTALLED_APPS, but settings are not configured. You must either define the environment variable DJANGO_SETTINGS_MODULE or call settings.configure() before accessing settings.
"""