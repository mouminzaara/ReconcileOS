"""
Django Admin configuration for Employee model.
"""

from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _
from .models import Employee, EmployeeStatus


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    """
    Admin configuration for managing Employee records.
    """
    list_display = (
        'full_name',
        'email',
        'department',
        'status',
        'created_at',
        'updated_at',
    )
    list_filter = ('status', 'department', 'created_at')
    search_fields = ('full_name', 'email', 'department')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        (_('Identity'), {
            'fields': ('id', 'full_name', 'email')
        }),
        (_('Organization & Status'), {
            'fields': ('department', 'status')
        }),
        (_('Audit Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['terminate_selected_employees', 'activate_selected_employees']

    @admin.action(description=_("Terminate selected employees"))
    def terminate_selected_employees(self, request, queryset):
        """Admin action to bulk-terminate selected active employees."""
        count = 0
        for employee in queryset:
            if employee.terminate():
                count += 1
        
        self.message_user(
            request,
            f"Successfully terminated {count} employee(s).",
            messages.SUCCESS
        )

    @admin.action(description=_("Set selected employees to ACTIVE"))
    def activate_selected_employees(self, request, queryset):
        """Admin action to reactivate employees if needed."""
        updated = queryset.update(status=EmployeeStatus.ACTIVE)
        self.message_user(
            request,
            f"Reactivated {updated} employee(s).",
            messages.SUCCESS
        )
