"""
DRF Serializers for ReconcileOS Invariant Rule Engine.
"""

from rest_framework import serializers
from .models import Rule, RuleSeverity


class RuleSerializer(serializers.ModelSerializer):
    """
    Serializer for Rule model.
    """
    severity_display = serializers.CharField(
        source='get_severity_display',
        read_only=True
    )
    rule_expression = serializers.SerializerMethodField()

    class Meta:
        model = Rule
        fields = [
            'id',
            'rule_code',
            'name',
            'description',
            'source_system',
            'condition_attribute',
            'condition_value',
            'target_system',
            'expected_attribute',
            'expected_value',
            'severity',
            'severity_display',
            'is_enabled',
            'rule_expression',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_rule_expression(self, obj):
        """
        Returns human-readable formal invariant expression:
        "WHEN HR.status == 'TERMINATED' THEN EXPECT VPN.status == 'DISABLED'"
        """
        return (
            f"WHEN {obj.source_system}.{obj.condition_attribute} == '{obj.condition_value}' "
            f"THEN EXPECT {obj.target_system}.{obj.expected_attribute} == '{obj.expected_value}'"
        )


class AIRuleGenerationRequestSerializer(serializers.Serializer):
    """
    Serializer for natural language rule generation request payload.
    """
    prompt = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=1000,
        help_text="Natural language security rule requirement (e.g. 'Terminated employees must not have access to company systems.')"
    )
