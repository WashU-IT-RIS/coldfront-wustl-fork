from coldfront.config.base import (
    INSTALLED_APPS,
    TEMPLATES,
    PROJECT_ROOT,
    STATICFILES_DIRS,
)

INSTALLED_APPS += [
    "coldfront.plugins.qumulo",
]

STATICFILES_DIRS += [
    PROJECT_ROOT("coldfront/plugins/qumulo/static"),
    PROJECT_ROOT("coldfront/plugins/qumulo/frontend/react/dist"),
]

TEMPLATES[0]["DIRS"] += [PROJECT_ROOT("coldfront/plugins/qumulo/templates")]
