from coldfront.config.base import (
    INSTALLED_APPS,
    TEMPLATES,
    PROJECT_ROOT,
    STATICFILES_DIRS,
)
from coldfront.config.env import ENV

INSTALLED_APPS += [
        "coldfront.plugins.coldfront_plugin_qumulo",
]

STATICFILES_DIRS += [
    PROJECT_ROOT("coldfront.plugins.coldfront_plugin_qumulo/static"),
]

TEMPLATES[0]["DIRS"] += [PROJECT_ROOT("coldfront.plugins.coldfront_plugin_qumulo/templates")]
