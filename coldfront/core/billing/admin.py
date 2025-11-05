import textwrap

from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from django.utils.translation import gettext_lazy as _

from coldfront.core.billing.models import (AllocationUsage)

@admin.register(AllocationUsage)
class AllocationUsageAdmin(SimpleHistoryAdmin):
    list_display = (
        'external_key',
        'tier',
        'source',
        'sponsor_pi',
        'billing_contact',
        'fileset_name',
        'service_rate_category',
        'usage_tb',
        'funding_number',
        'exempt',
        'subsidized',
        'is_condo_group',
        'parent_id_key',
        'quota',
        'billing_cycle',
        'usage_date',
        'storage_cluster',
    )
    search_fields = (
        'external_key',
        'source',
        'sponsor_pi',
        'billing_contact',
        'fileset_name',
        'service_rate_category',
        'funding_number',
        'quota',
        'billing_cycle',
        'storage_cluster',
        'tier',
    )
    list_filter = (
        'exempt',
        'subsidized',
        'is_condo_group',
        'storage_cluster',
        'tier',
    )
    ordering = ('-usage_date', 'sponsor_pi', 'service_rate_category')
    date_hierarchy = 'usage_date'
    fieldsets = (
        (None, {
            'fields': (
                ('external_key', 'source'),
                ('sponsor_pi', 'billing_contact'),
                ('fileset_name', 'service_rate_category', 'usage_tb'),
                ('funding_number', 'exempt', 'subsidized'),
                ('is_condo_group', 'parent_id_key'),
                ('quota', 'billing_cycle'),
                ('usage_date', 'storage_cluster'),
            ),
            'description': textwrap.dedent("""
                <p class="help">
                    <strong>Note:</strong> The <em>parent_id_key</em> field may be null if the allocation is not part of a condo group.
                </p>
            """),
        }),
    )
