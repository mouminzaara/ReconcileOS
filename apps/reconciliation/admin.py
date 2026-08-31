"""
Django Admin interface for ReconcileOS Integrity Violations.
"""

from django.contrib import admin
from .models import IntegrityViolation


@admin.register(IntegrityViolation)
class IntegrityViolationAdmin(admin.ModelAdmin):
    """
    Admin interface for IntegrityViolation model.
    """
    list_display = [
        'id',
        'employee',
        'rule',
        'affected_system',
        'expected_state',
        'actual_state',
        'severity',
        'status',
        'detected_at',
        'updated_at',
    ]
    list_filter = ['status', 'severity', 'affected_system', 'rule__rule_code']
    search_fields = [
        'employee__full_name',
        'employee__email',
        'affected_system',
        'rule__rule_code',
        'rule__name'
    ]
    ordering = ['-detected_at']
    readonly_fields = ['id', 'detected_at', 'updated_at']

    actions = ['mark_as_resolved']

    @admin.action(description="Mark selected violations as RESOLVED")
    def mark_as_resolved(self, request, queryset):
        updated = queryset.update(status='RESOLVED')
        self.message_user(request, f"Successfully resolved {updated} integrity violation(s).")
