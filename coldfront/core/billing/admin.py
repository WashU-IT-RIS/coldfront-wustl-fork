import textwrap

from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from django.utils.translation import gettext_lazy as _

from coldfront.core.billing.models import (AllocationUsage)

@admin.register(AllocationUsage)
class AllocationUsageAdmin(SimpleHistoryAdmin):
    list_display = (
        'source',
        'external_key',
        'tier',
        'filesystem_path',
        'sponsor_pi',
        'billing_contact',
        'fileset_name',
        'storage_cluster',
        'status',
        'service_rate_category',
        'usage_date',
        'usage_tb',
        'exempt',
        'subsidized',
        'is_condo_group',
        'parent_id_key',
        'quota',
        'funding_number',
        'billing_cycle',
    )
    search_fields = (
        'external_key',
        'source',
        'sponsor_pi',
        'billing_contact',
        'filesystem_path',
        'fileset_name',
        'status',
        'service_rate_category',
        'funding_number',
        'quota',
        'billing_cycle',
        'storage_cluster',
        'tier',
    )
    list_filter = (
        'source',
        'tier',
        'storage_cluster',
        'service_rate_category',
        'exempt',
        'subsidized',
        'is_condo_group',
        'billing_cycle',
    )
    ordering = ('-usage_date', 'sponsor_pi', 'service_rate_category')
    date_hierarchy = 'usage_date'
    fieldsets = (
        (None, {
            'fields': (
                ('external_key', 'source', 'tier'),
                ('sponsor_pi', 'billing_contact'),
                ('storage_cluster', 'filesystem_path'),
                ('fileset_name', 'service_rate_category', 'usage_tb'),
                ('funding_number', 'exempt', 'subsidized'),
                ('is_condo_group', 'parent_id_key'),
                ('quota', 'billing_cycle'),
                ('usage_date', 'status'),
            ),
            'description': textwrap.dedent("""
                <p class="help">
                    <strong>Note:</strong> The <em>parent_id_key</em> field may be null if the allocation is not part of a condo group.
                </p>
            """),
        }),
    )
