from django.urls import path

from coldfront_plugin_qumulo.views import allocation_view, update_allocation_view, allocation_table_view

app_name = "coldfront_plugin_qumulo"
urlpatterns = [
    path("allocation", allocation_view.AllocationView.as_view(), name="allocation"),
    path(
        "allocation/<int:allocation_id>/",
        update_allocation_view.UpdateAllocationView.as_view(),
        name="updateAllocation",
    ),
    path("allocation-table-list", allocation_table_view.AllocationTableView.as_view(), name="allocation-table-list")
]