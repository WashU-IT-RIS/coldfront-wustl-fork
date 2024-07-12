from coldfront.config.base import (
    INSTALLED_APPS,
    TEMPLATES,
    PROJECT_ROOT,
    STATICFILES_DIRS,
)
from coldfront.config.env import ENV

if "coldfront_plugin_qumulo" not in INSTALLED_APPS:
    INSTALLED_APPS += [
        "coldfront_plugin_qumulo",
    ]

    STATICFILES_DIRS += [
        PROJECT_ROOT("coldfront_plugin_qumulo/static"),
    ]

    TEMPLATES[0]["DIRS"] += [PROJECT_ROOT("coldfront_plugin_qumulo/templates")]
