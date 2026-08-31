"""
Django Admin interface registration for ReconcileOS Invariant Rule Engine.
"""

from django.contrib import admin
from .models import Rule


@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    """
    Admin interface for Rule model.
    """
    list_display = [
        'rule_code',
        'name',
        'source_system',
        'condition_attribute',
        'condition_value',
        'target_system',
        'expected_attribute',
        'expected_value',
        'severity',
        'is_enabled',
        'updated_at',
    ]
    list_filter = ['is_enabled', 'severity', 'source_system', 'target_system']
    search_fields = ['rule_code', 'name', 'description', 'source_system', 'target_system']
    ordering = ['rule_code']
    readonly_fields = ['id', 'created_at', 'updated_at']

    actions = ['enable_rules', 'disable_rules']

    @admin.action(description="Enable selected invariant rules")
    def enable_rules(self, request, queryset):
        updated = queryset.update(is_enabled=True)
        self.message_user(request, f"Successfully enabled {updated} invariant rule(s).")

    @admin.action(description="Disable selected invariant rules")
    def disable_rules(self, request, queryset):
        updated = queryset.update(is_enabled=False)
        self.message_user(request, f"Successfully disabled {updated} invariant rule(s).")
