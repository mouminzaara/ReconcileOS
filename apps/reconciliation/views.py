"""
API Views for ReconcileOS Reconciliation Engine & Integrity Violations.
"""

from rest_framework import viewsets, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend

from .models import IntegrityViolation
from .collectors import StateCollector, EmployeeNotFoundException, InvalidEmployeeIDException
from .engine import ReconciliationEngine
from .serializers import CollectedStateSerializer, IntegrityViolationSerializer
from apps.accounts.permissions import IsOperatorUserRole, IsViewerUserRole


class CollectedStateListView(APIView):
    """
    API View to retrieve collected multi-system state for all employees.
    GET /api/v1/reconciliation/state/
    """
    permission_classes = [IsViewerUserRole]

    def get(self, request):
        collector = StateCollector()
        states = collector.collect_all_states()
        serializer = CollectedStateSerializer(states, many=True)
        return Response({
            "count": len(states),
            "results": serializer.data
        }, status=status.HTTP_200_OK)


class CollectedStateDetailView(APIView):
    """
    API View to retrieve collected multi-system state for a specific employee.
    GET /api/v1/reconciliation/state/<employee_id>/
    """
    permission_classes = [IsViewerUserRole]

    def get(self, request, employee_id):
        collector = StateCollector()
        try:
            state = collector.collect_employee_state(employee_id)
            serializer = CollectedStateSerializer(state)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except (EmployeeNotFoundException, InvalidEmployeeIDException) as exc:
            raise Http404(str(exc))


class IntegrityViolationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API ViewSet for inspecting Integrity Violations (authorization drift records).
    """
    queryset = IntegrityViolation.objects.select_related('employee', 'rule').all()
    serializer_class = IntegrityViolationSerializer

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'severity', 'affected_system', 'employee', 'rule__rule_code']
    search_fields = ['employee__full_name', 'employee__email', 'affected_system', 'rule__rule_code', 'rule__name']
    ordering_fields = ['detected_at', 'updated_at', 'severity', 'status']
    ordering = ['-detected_at']

    def get_permissions(self):
        if self.action in ['run_reconciliation']:
            return [IsOperatorUserRole()]
        return [IsViewerUserRole()]

    @action(detail=False, methods=['post'], url_path='run')
    def run_reconciliation(self, request):
        """
        Action endpoint to execute reconciliation engine audit across all employees.
        """
        engine = ReconciliationEngine()
        employee_id = request.data.get('employee_id') or request.query_params.get('employee_id')

        if employee_id:
            try:
                report = engine.evaluate_employee_rules(employee_id)
                return Response(report, status=status.HTTP_200_OK)
            except (EmployeeNotFoundException, InvalidEmployeeIDException) as exc:
                return Response({"error": str(exc)}, status=status.HTTP_404_NOT_FOUND)

        reports = engine.evaluate_all()
        total_violations = sum(r['violations_detected_count'] for r in reports)
        return Response({
            "status": "success",
            "message": f"Reconciliation engine completed audit. {total_violations} active violation(s) detected.",
            "total_employees_evaluated": len(reports),
            "total_violations_detected": total_violations,
            "reports": reports
        }, status=status.HTTP_200_OK)


class RunReconciliationView(APIView):
    """
    Explicit API View to trigger reconciliation audit check.
    POST /api/v1/reconciliation/run/
    """
    permission_classes = [IsOperatorUserRole]

    def post(self, request):
        engine = ReconciliationEngine()
        employee_id = request.data.get('employee_id')

        if employee_id:
            try:
                report = engine.evaluate_employee_rules(employee_id)
                return Response(report, status=status.HTTP_200_OK)
            except (EmployeeNotFoundException, InvalidEmployeeIDException) as exc:
                return Response({"error": str(exc)}, status=status.HTTP_404_NOT_FOUND)

        reports = engine.evaluate_all()
        total_violations = sum(r['violations_detected_count'] for r in reports)
        return Response({
            "status": "success",
            "message": f"Reconciliation engine completed audit. {total_violations} active violation(s) detected.",
            "total_employees_evaluated": len(reports),
            "total_violations_detected": total_violations,
            "reports": reports
        }, status=status.HTTP_200_OK)


class ContinuousMonitorView(APIView):
    """
    API View to trigger a continuous integrity monitoring cycle.
    POST /api/v1/reconciliation/monitor/
    """
    permission_classes = [IsOperatorUserRole]

    def post(self, request):
        from .monitor import ContinuousMonitor
        employee_id = request.data.get('employee_id')
        auto_approve = request.data.get('auto_approve', False)

        monitor = ContinuousMonitor()
        summary = monitor.run_monitoring_cycle(
            employee_id=employee_id,
            auto_approve_policy=auto_approve
        )
        return Response(summary, status=status.HTTP_200_OK)
