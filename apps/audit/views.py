"""
Views for Audit Log REST API.
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import AuditLog
from .serializers import AuditLogSerializer
from .services import AuditLogger


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only API ViewSet for inspecting append-only audit log records.

    Disallows creation, updates, and deletions via REST interface.
    Provides custom endpoint `/api/audit/logs/verify_chain/` to audit tamper evidence.
    """
    queryset = AuditLog.objects.all().select_related('employee')
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['event_type', 'actor', 'system', 'result', 'correlation_id', 'employee']
    search_fields = [
        'actor',
        'system',
        'action',
        'correlation_id',
        'result',
        'employee__full_name',
        'employee__email'
    ]
    ordering_fields = ['timestamp', 'event_type', 'actor', 'system']
    ordering = ['-timestamp', '-id']

    @action(detail=False, methods=['get'], url_path='verify_chain')
    def verify_chain(self, request):
        """
        Custom action to audit the cryptographic SHA-256 hash chain across all stored log entries.
        """
        is_valid, message, details = AuditLogger.verify_chain_integrity()
        return Response(
            {
                "is_valid": is_valid,
                "message": message,
                "details": details
            },
            status=status.HTTP_200_OK if is_valid else status.HTTP_409_CONFLICT
        )
