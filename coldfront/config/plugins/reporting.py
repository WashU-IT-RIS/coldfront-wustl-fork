from coldfront.config.base import (
    INSTALLED_APPS,
    TEMPLATES,
    PROJECT_ROOT,
    STATICFILES_DIRS,
)

INSTALLED_APPS += [
    "coldfront.plugins.reporting",
]

STATICFILES_DIRS += [
    PROJECT_ROOT("coldfront/plugins/reporting/frontend/react/dist"),
]

TEMPLATES[0]["DIRS"] += [PROJECT_ROOT("coldfront/plugins/reporting/templates")]