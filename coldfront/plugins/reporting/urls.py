from django.urls import path

from coldfront.plugins.reporting.views import (
    reports_view,
)


app_name = "reporting"
urlpatterns = [
    path(
        "reports",
        reports_view.ReportsView.as_view(),
        name="reports",
    ),
]
