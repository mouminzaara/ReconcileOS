"""
API Views for ReconcileOS Human-in-the-Loop Approvals Engine.
"""

from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django.core.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend

from .models import ApprovalRequest, ApprovalDecision
from .services import ApprovalService
from .serializers import ApprovalRequestSerializer, ApprovalActionSerializer
from apps.accounts.permissions import IsAdminUserRole, IsViewerUserRole


class ApprovalRequestViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API ViewSet for inspecting and deciding Human-in-the-Loop Approval Requests.
    """
    queryset = ApprovalRequest.objects.select_related(
        'repair_plan',
        'repair_plan__employee',
        'repair_plan__violation',
        'requested_by',
        'decided_by'
    ).all()
    serializer_class = ApprovalRequestSerializer

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['decision', 'repair_plan', 'repair_plan__target_system', 'repair_plan__risk_level']
    search_fields = [
        'repair_plan__employee__full_name',
        'repair_plan__employee__email',
        'repair_plan__action',
        'repair_plan__target_system',
        'comment'
    ]
    ordering_fields = ['created_at', 'updated_at', 'decided_at', 'decision']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ['approve', 'reject']:
            return [IsAdminUserRole()]
        return [IsViewerUserRole()]

    @action(detail=False, methods=['get'], url_path='pending')
    def pending(self, request):
        """
        Action endpoint to list all PENDING approval requests.
        """
        pending_requests = self.get_queryset().filter(decision=ApprovalDecision.PENDING)
        page = self.paginate_queryset(pending_requests)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(pending_requests, many=True)
        return Response({
            "count": pending_requests.count(),
            "results": serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        """
        Action endpoint to approve a pending repair plan.
        """
        approval_request = self.get_object()
        action_serializer = ApprovalActionSerializer(data=request.data)
        action_serializer.is_valid(raise_exception=True)
        comment = action_serializer.validated_data.get('comment', '')

        decided_by = request.user if request.user.is_authenticated else None

        try:
            updated_request = ApprovalService.approve_request(
                approval_request=approval_request,
                decided_by=decided_by,
                comment=comment
            )
            serializer = self.get_serializer(updated_request)
            return Response({
                "status": "success",
                "message": f"Approval request {approval_request.id} APPROVED. Repair plan status is now APPROVED.",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except ValidationError as exc:
            return Response({
                "status": "error",
                "message": str(exc.message if hasattr(exc, 'message') else exc)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        """
        Action endpoint to reject a pending repair plan.
        """
        approval_request = self.get_object()
        action_serializer = ApprovalActionSerializer(data=request.data)
        action_serializer.is_valid(raise_exception=True)
        comment = action_serializer.validated_data.get('comment', '')

        decided_by = request.user if request.user.is_authenticated else None

        try:
            updated_request = ApprovalService.reject_request(
                approval_request=approval_request,
                decided_by=decided_by,
                comment=comment
            )
            serializer = self.get_serializer(updated_request)
            return Response({
                "status": "success",
                "message": f"Approval request {approval_request.id} REJECTED. Repair plan status is now REJECTED.",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except ValidationError as exc:
            return Response({
                "status": "error",
                "message": str(exc.message if hasattr(exc, 'message') else exc)
            }, status=status.HTTP_400_BAD_REQUEST)
