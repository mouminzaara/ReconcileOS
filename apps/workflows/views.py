"""
API Views for ReconcileOS Repair Planning, Execution & Verification Engine.
"""

import uuid
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend

from apps.employees.models import Employee
from .models import RepairPlan
from .planner import RepairPlanner
from .executor import RepairExecutor, IneligiblePlanExecutionException, ExecutionException
from .verifier import PostRepairVerifier
from .serializers import RepairPlanSerializer, RepairExecutionLogSerializer, RepairVerificationSerializer
from apps.accounts.permissions import IsAdminUserRole, IsOperatorUserRole, IsViewerUserRole


class RepairPlanViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API ViewSet for inspecting, generating, executing, and verifying Repair Plans.
    """
    queryset = RepairPlan.objects.select_related('employee', 'violation', 'violation__rule').all()
    serializer_class = RepairPlanSerializer

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'risk_level', 'target_system', 'employee']
    search_fields = ['employee__full_name', 'employee__email', 'target_system', 'action', 'reason']
    ordering_fields = ['created_at', 'updated_at', 'risk_level', 'status']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ['execute_plan', 'verify_plan']:
            return [IsAdminUserRole()]
        if self.action in ['generate_plans']:
            return [IsOperatorUserRole()]
        return [IsViewerUserRole()]

    @action(detail=False, methods=['post'], url_path='generate')
    def generate_plans(self, request):
        """
        Action endpoint to generate repair plans for open integrity violations.
        Requires valid employee_id.
        """
        employee_id = request.data.get('employee_id') or request.query_params.get('employee_id')
        if not employee_id:
            return Response({
                "status": "error",
                "message": "Missing required parameter 'employee_id'."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate employee_id format
        try:
            val_uuid = uuid.UUID(str(employee_id))
        except (ValueError, AttributeError, TypeError):
            return Response({
                "status": "error",
                "message": f"Invalid employee_id format: '{employee_id}'. Must be a valid UUID."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verify employee exists in database
        if not Employee.objects.filter(id=val_uuid).exists():
            return Response({
                "status": "error",
                "message": f"Employee with ID '{employee_id}' not found."
            }, status=status.HTTP_404_NOT_FOUND)

        planner = RepairPlanner()
        plans = planner.plan_all_open_violations(employee_id=str(val_uuid))

        serializer = self.get_serializer(plans, many=True)
        return Response({
            "status": "success",
            "message": f"Generated/retrieved {len(plans)} repair plan(s).",
            "count": len(plans),
            "results": serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='execute')
    def execute_plan(self, request, pk=None):
        """
        Action endpoint to execute an approved repair plan against its target system connector.
        Enforces approval and status eligibility. Requires ADMIN role.
        """
        repair_plan = self.get_object()
        executor = RepairExecutor()

        executed_by = request.user if request.user.is_authenticated else None

        try:
            log = executor.execute_plan(repair_plan=repair_plan, executed_by=executed_by)
            log_data = RepairExecutionLogSerializer(log).data
            repair_plan.refresh_from_db()
            plan_data = self.get_serializer(repair_plan).data

            if log.status == 'SUCCESS':
                return Response({
                    "status": "success",
                    "message": f"Repair plan {repair_plan.id} executed and verified successfully.",
                    "plan_status": repair_plan.status,
                    "execution_log": log_data,
                    "plan": plan_data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "status": "error",
                    "message": f"Repair plan {repair_plan.id} execution failed.",
                    "plan_status": repair_plan.status,
                    "execution_log": log_data,
                    "plan": plan_data
                }, status=status.HTTP_400_BAD_REQUEST)

        except IneligiblePlanExecutionException as exc:
            return Response({
                "status": "error",
                "message": str(exc)
            }, status=status.HTTP_400_BAD_REQUEST)
        except ExecutionException as exc:
            return Response({
                "status": "error",
                "message": str(exc)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='verify')
    def verify_plan(self, request, pk=None):
        """
        Action endpoint to perform empirical post-repair verification re-querying target system.
        """
        repair_plan = self.get_object()
        verifier = PostRepairVerifier()
        verification = verifier.verify_repair(repair_plan)

        repair_plan.refresh_from_db()
        verification_data = RepairVerificationSerializer(verification).data

        status_code = status.HTTP_200_OK if verification.result == 'VERIFIED' else status.HTTP_400_BAD_REQUEST
        return Response({
            "status": "success" if verification.result == 'VERIFIED' else "error",
            "message": verification.details,
            "verification_result": verification.result,
            "plan_status": repair_plan.status,
            "verification": verification_data
        }, status=status_code)
