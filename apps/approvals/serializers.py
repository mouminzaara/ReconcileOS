"""
Serializers for ReconcileOS Human-in-the-Loop Approvals Engine.
"""

from rest_framework import serializers
from apps.workflows.serializers import RepairPlanSerializer
from .models import ApprovalRequest


class ApprovalRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for ApprovalRequest model.
    Includes nested repair plan details and user email representations.
    """
    repair_plan_detail = RepairPlanSerializer(source='repair_plan', read_only=True)
    requested_by_email = serializers.ReadOnlyField(source='requested_by.email', default=None)
    decided_by_email = serializers.ReadOnlyField(source='decided_by.email', default=None)

    class Meta:
        model = ApprovalRequest
        fields = [
            'id',
            'repair_plan',
            'repair_plan_detail',
            'requested_by',
            'requested_by_email',
            'decided_by',
            'decided_by_email',
            'decision',
            'decided_at',
            'comment',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'decision',
            'decided_at',
            'created_at',
            'updated_at',
        ]


class ApprovalActionSerializer(serializers.Serializer):
    """
    Serializer for approve/reject action payload inputs.
    """
    comment = serializers.CharField(required=False, allow_blank=True, default='')
