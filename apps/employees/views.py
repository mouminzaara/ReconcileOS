import uuid
import logging
from django.db import transaction
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Employee, EmployeeStatus
from .serializers import EmployeeSerializer, EmployeeTerminateSerializer
from apps.accounts.permissions import IsAdminUserRole, IsViewerUserRole
from apps.audit.models import AuditEventType
from apps.audit.services import AuditLogger
from apps.reconciliation.engine import ReconciliationEngine
from apps.workflows.planner import RepairPlanner

logger = logging.getLogger(__name__)


class EmployeeViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for managing Employee records in the primary HR system.
    Prefetches connected downstream systems to eliminate N+1 database queries.
    """
    queryset = Employee.objects.select_related(
        'vpn_access',
        'github_membership',
        'cloud_access',
        'slack_account'
    ).all()
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
        Records an append-only audit event and triggers deterministic drift reconciliation.
        """
        employee = self.get_object()
        serializer = EmployeeTerminateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reason = serializer.validated_data.get('reason', '')
        was_active = (employee.status == EmployeeStatus.ACTIVE)
        previous_status = employee.status

        correlation_id = str(uuid.uuid4())
        actor = request.user.username if request.user and request.user.is_authenticated else 'SYSTEM'

        # 1. Update employee status and record audit log event in an atomic transaction
        with transaction.atomic():
            status_changed = employee.terminate()
            if status_changed:
                AuditLogger.log_event(
                    event_type=AuditEventType.EMPLOYEE_TERMINATED,
                    actor=actor,
                    employee=employee,
                    system='HR',
                    action='TERMINATE_EMPLOYEE',
                    previous_state=previous_status,
                    new_state=EmployeeStatus.TERMINATED,
                    result='SUCCESS',
                    correlation_id=correlation_id,
                    additional_metadata={
                        'reason': reason,
                        'employee_id': str(employee.id),
                        'email': employee.email,
                        'department': employee.department
                    }
                )

        response_data = {
            "status": "success",
            "message": "Employee terminated successfully." if status_changed else "Employee is already terminated.",
            "status_changed": status_changed,
            "was_active": was_active,
            "reason": reason if reason else None,
            "employee": EmployeeSerializer(employee).data,
            "correlation_id": correlation_id
        }

        # 2. Trigger reconciliation only if a lifecycle transition occurred
        if status_changed:
            try:
                engine = ReconciliationEngine()
                recon_report = engine.evaluate_employee_rules(employee.id, correlation_id=correlation_id)

                planner = RepairPlanner()
                plans = planner.plan_all_open_violations(employee_id=str(employee.id), correlation_id=correlation_id)

                response_data["reconciliation"] = {
                    "status": "completed",
                    "rules_evaluated_count": recon_report.get("rules_evaluated_count", 0),
                    "violations_detected_count": recon_report.get("violations_detected_count", 0),
                    "violations": recon_report.get("violations", []),
                    "repair_plans_generated_count": len(plans),
                    "repair_plans": [str(p.id) for p in plans]
                }
            except Exception as exc:
                logger.error(f"Reconciliation error after terminating {employee.id}: {exc}", exc_info=True)
                response_data["reconciliation"] = {
                    "status": "error",
                    "message": f"Reconciliation error: {exc}",
                    "violations_detected_count": 0,
                    "repair_plans_generated_count": 0
                }

        return Response(response_data, status=status.HTTP_200_OK)
