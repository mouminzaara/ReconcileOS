"""
Django Admin configuration for VPNAccess model.
"""

from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _
from .models import VPNAccess, VPNAccessStatus


@admin.register(VPNAccess)
class VPNAccessAdmin(admin.ModelAdmin):
    """
    Admin interface configuration for managing simulated VPN access records.
    """
    list_display = (
        'get_employee_name',
        'get_employee_email',
        'get_employee_status',
        'get_employee_department',
        'status',
        'updated_at',
        'created_at',
    )
    list_filter = (
        'status',
        'employee__status',
        'employee__department',
        'created_at',
        'updated_at',
    )
    search_fields = (
        'employee__full_name',
        'employee__email',
        'employee__department',
    )
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-updated_at',)

    fieldsets = (
        (_('Employee Binding'), {
            'fields': ('id', 'employee')
        }),
        (_('VPN Access State'), {
            'fields': ('status',)
        }),
        (_('Audit Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['enable_selected_vpn_access', 'disable_selected_vpn_access']

    @admin.display(description=_('Employee Name'), ordering='employee__full_name')
    def get_employee_name(self, obj):
        return obj.employee.full_name

    @admin.display(description=_('Employee Email'), ordering='employee__email')
    def get_employee_email(self, obj):
        return obj.employee.email

    @admin.display(description=_('HR Status'), ordering='employee__status')
    def get_employee_status(self, obj):
        return obj.employee.status

    @admin.display(description=_('Department'), ordering='employee__department')
    def get_employee_department(self, obj):
        return obj.employee.department

    @admin.action(description=_("Enable VPN access for selected records"))
    def enable_selected_vpn_access(self, request, queryset):
        """Bulk action to enable VPN access."""
        count = 0
        for vpn_access in queryset:
            if vpn_access.enable():
                count += 1
        self.message_user(
            request,
            f"Successfully enabled VPN access for {count} record(s).",
            messages.SUCCESS
        )

    @admin.action(description=_("Disable VPN access for selected records"))
    def disable_selected_vpn_access(self, request, queryset):
        """Bulk action to disable VPN access."""
        count = 0
        for vpn_access in queryset:
            if vpn_access.disable():
                count += 1
        self.message_user(
            request,
            f"Successfully disabled VPN access for {count} record(s).",
            messages.SUCCESS
        )
