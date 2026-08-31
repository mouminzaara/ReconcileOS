"""
API Views and ViewSets for Simulated VPN Connector.
"""

import uuid
from django.http import Http404
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.employees.models import Employee
from .models import VPNAccess, VPNAccessStatus
from .serializers import VPNAccessSerializer


class VPNAccessViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for managing Simulated VPN Access states.
    
    Standard Endpoints:
    - GET    /api/v1/vpn/                       -> List all VPN access records (filterable, searchable)
    - POST   /api/v1/vpn/                       -> Create explicit VPN access record
    - GET    /api/v1/vpn/<employee_id>/         -> Retrieve VPN access state (auto-initializes to DISABLED if absent)
    - PUT    /api/v1/vpn/<employee_id>/         -> Update VPN access record
    - PATCH  /api/v1/vpn/<employee_id>/         -> Partial update VPN access record
    - DELETE /api/v1/vpn/<employee_id>/         -> Remove VPN access record
    
    Action Endpoints:
    - POST   /api/v1/vpn/<employee_id>/enable/  -> Explicitly enable VPN access for employee
    - POST   /api/v1/vpn/<employee_id>/disable/ -> Explicitly disable VPN access for employee
    """
    queryset = VPNAccess.objects.select_related('employee').all()
    serializer_class = VPNAccessSerializer
    lookup_field = 'employee_id'
    lookup_url_kwarg = 'employee_id'

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'employee__department', 'employee__status']
    search_fields = ['employee__full_name', 'employee__email', 'employee__department']
    ordering_fields = ['created_at', 'updated_at', 'status', 'employee__full_name']
    ordering = ['-updated_at']

    def get_employee_or_404(self, employee_id):
        """
        Validates employee_id format and retrieves the Employee instance.
        Raises Http404 if invalid UUID or if employee does not exist.
        """
        try:
            val = uuid.UUID(str(employee_id))
        except (ValueError, AttributeError, TypeError):
            raise Http404(f"Invalid employee ID format: '{employee_id}'. Must be a valid UUID.")

        try:
            return Employee.objects.get(pk=val)
        except Employee.DoesNotExist:
            raise Http404(f"Employee with ID '{employee_id}' does not exist.")

    def get_object(self):
        """
        Retrieves the VPNAccess record corresponding to the employee_id in URL.
        
        Auto-Initialization Behavior:
        If the employee exists in the HR system but does not yet possess a VPN
        access record, this method automatically creates a new record with status
        set to DISABLED (defaulting to least-privilege zero-trust state).
        """
        employee_id = self.kwargs.get(self.lookup_url_kwarg)
        employee = self.get_employee_or_404(employee_id)

        vpn_access, _ = VPNAccess.objects.get_or_create(
            employee=employee,
            defaults={'status': VPNAccessStatus.DISABLED}
        )
        return vpn_access

    @action(detail=True, methods=['post'], url_path='enable')
    def enable(self, request, employee_id=None):
        """
        Explicit action endpoint to enable VPN access for an employee.
        Auto-initializes the record to DISABLED first if absent, then sets to ENABLED.
        """
        vpn_access = self.get_object()
        status_changed = vpn_access.enable()

        response_data = {
            "status": "success",
            "message": "VPN access enabled successfully." if status_changed else "VPN access is already enabled.",
            "status_changed": status_changed,
            "action": "ENABLE",
            "vpn_access": VPNAccessSerializer(vpn_access).data
        }
        return Response(response_data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='disable')
    def disable(self, request, employee_id=None):
        """
        Explicit action endpoint to disable VPN access for an employee.
        Auto-initializes the record to DISABLED first if absent, then sets to DISABLED.
        """
        vpn_access = self.get_object()
        status_changed = vpn_access.disable()

        response_data = {
            "status": "success",
            "message": "VPN access disabled successfully." if status_changed else "VPN access is already disabled.",
            "status_changed": status_changed,
            "action": "DISABLE",
            "vpn_access": VPNAccessSerializer(vpn_access).data
        }
        return Response(response_data, status=status.HTTP_200_OK)
