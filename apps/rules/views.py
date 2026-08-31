"""
API Views and ViewSets for ReconcileOS Invariant Rule Engine.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Rule
from .serializers import RuleSerializer, AIRuleGenerationRequestSerializer
from .ai_service import AIRuleGenerator, AIRuleGenerationException
from apps.accounts.permissions import IsAdminUserRole, IsViewerUserRole


class RuleViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for managing invariant rules.
    """
    queryset = Rule.objects.all()
    serializer_class = RuleSerializer
    lookup_field = 'pk'

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_enabled', 'severity', 'source_system', 'target_system']
    search_fields = ['rule_code', 'name', 'description', 'source_system', 'target_system']
    ordering_fields = ['rule_code', 'created_at', 'updated_at', 'severity', 'name']
    ordering = ['rule_code']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'toggle', 'generate_draft']:
            return [IsAdminUserRole()]
        return [IsViewerUserRole()]

    @action(detail=True, methods=['post'], url_path='toggle')
    def toggle(self, request, pk=None):
        """
        Action endpoint to toggle the is_enabled state of a rule.
        """
        rule = self.get_object()
        rule.is_enabled = not rule.is_enabled
        rule.save(update_fields=['is_enabled', 'updated_at'])

        status_text = "enabled" if rule.is_enabled else "disabled"
        return Response({
            "status": "success",
            "message": f"Rule {rule.rule_code} is now {status_text}.",
            "is_enabled": rule.is_enabled,
            "rule": RuleSerializer(rule).data
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='generate_draft')
    def generate_draft(self, request):
        """
        Action endpoint allowing administrators to generate a proposed structured rule from natural language prompt.
        
        The generated rule is created strictly in DRAFT state (is_enabled=False).
        Human administrator review and explicit approval (toggle/activate) is required before evaluation.
        """
        serializer = AIRuleGenerationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": "error",
                "message": "Invalid request payload.",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        prompt = serializer.validated_data['prompt']
        actor = request.user.username if request.user and hasattr(request.user, 'username') else 'ADMIN'

        try:
            draft_rule = AIRuleGenerator.generate_draft_rule(prompt, creator_actor=actor)
            return Response({
                "status": "success",
                "message": f"AI draft rule '{draft_rule.rule_code}' created successfully. Requires human administrator review and activation.",
                "is_enabled": False,
                "human_review_required": True,
                "rule": RuleSerializer(draft_rule).data
            }, status=status.HTTP_201_CREATED)
        except AIRuleGenerationException as exc:
            return Response({
                "status": "error",
                "message": str(exc),
                "human_review_required": False
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response({
                "status": "error",
                "message": f"AI rule generation failed: {exc}",
                "human_review_required": False
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
