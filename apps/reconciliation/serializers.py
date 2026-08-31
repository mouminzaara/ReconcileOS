"""
DRF Serializers for ReconcileOS Reconciliation Engine & Integrity Violations.
"""

from rest_framework import serializers
from .models import IntegrityViolation, ViolationStatus


class SystemStateDetailSerializer(serializers.Serializer):
    connected = serializers.BooleanField()
    access_status = serializers.CharField()
    record_id = serializers.CharField(allow_null=True)
    created_at = serializers.CharField(allow_null=True)
    updated_at = serializers.CharField(allow_null=True)


class CollectedStateSerializer(serializers.Serializer):
    employee_id = serializers.UUIDField()
    employee_name = serializers.CharField()
    employee_email = serializers.EmailField()
    department = serializers.CharField()
    employee_status = serializers.CharField()
    collected_at = serializers.DateTimeField()
    systems = serializers.DictField(child=SystemStateDetailSerializer())


class IntegrityViolationSerializer(serializers.ModelSerializer):
    """
    Serializer for IntegrityViolation model.
    """
    employee_id = serializers.UUIDField(source='employee.id', read_only=True)
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_email = serializers.CharField(source='employee.email', read_only=True)
    employee_department = serializers.CharField(source='employee.department', read_only=True)
    employee_status = serializers.CharField(source='employee.status', read_only=True)
    
    rule_code = serializers.CharField(source='rule.rule_code', read_only=True)
    rule_name = serializers.CharField(source='rule.name', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = IntegrityViolation
        fields = [
            'id',
            'employee',
            'employee_id',
            'employee_name',
            'employee_email',
            'employee_department',
            'employee_status',
            'rule',
            'rule_code',
            'rule_name',
            'affected_system',
            'expected_state',
            'actual_state',
            'severity',
            'severity_display',
            'status',
            'status_display',
            'detected_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'detected_at', 'updated_at']
