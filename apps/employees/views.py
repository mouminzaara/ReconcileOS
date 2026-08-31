"""
API Views and ViewSets for Employee management.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Employee, EmployeeStatus
from .serializers import EmployeeSerializer, EmployeeTerminateSerializer
from apps.accounts.permissions import IsAdminUserRole, IsViewerUserRole


class EmployeeViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for managing Employee records in the primary HR system.
    """
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'department']
    search_fields = ['full_name', 'email', 'department']
    ordering_fields = ['created_at', 'updated_at', 'full_name', 'department', 'status']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'terminate']:
            return [IsAdminUserRole()]
        return [IsViewerUserRole()]

    @action(detail=True, methods=['post'], url_path='terminate')
    def terminate(self, request, pk=None):
        """
        Explicit action endpoint to terminate an employee.
        """
        employee = self.get_object()
        serializer = EmployeeTerminateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        reason = serializer.validated_data.get('reason', '')
        was_active = (employee.status == EmployeeStatus.ACTIVE)
        
        status_changed = employee.terminate()
        
        response_data = {
            "status": "success",
            "message": "Employee terminated successfully." if status_changed else "Employee is already terminated.",
            "status_changed": status_changed,
            "was_active": was_active,
            "reason": reason if reason else None,
            "employee": EmployeeSerializer(employee).data
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
