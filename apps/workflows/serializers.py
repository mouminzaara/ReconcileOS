"""
Serializers for ReconcileOS Repair Planning Engine.
"""

from rest_framework import serializers
from apps.employees.serializers import EmployeeSerializer
from apps.reconciliation.serializers import IntegrityViolationSerializer
from .models import RepairPlan, RepairExecutionLog, RepairVerification


class RepairExecutionLogSerializer(serializers.ModelSerializer):
    """
    Serializer for RepairExecutionLog model.
    """
    executed_by_email = serializers.ReadOnlyField(source='executed_by.email', default=None)
    operation_id = serializers.ReadOnlyField()
    error = serializers.ReadOnlyField(source='error_details')

    class Meta:
        model = RepairExecutionLog
        fields = [
            'id',
            'operation_id',
            'repair_plan',
            'executed_by',
            'executed_by_email',
            'attempt_number',
            'status',
            'output_message',
            'error',
            'error_details',
            'started_at',
            'completed_at',
        ]
        read_only_fields = fields


class RepairVerificationSerializer(serializers.ModelSerializer):
    """
    Serializer for RepairVerification model.
    """
    class Meta:
        model = RepairVerification
        fields = [
            'id',
            'repair_plan',
            'expected_state',
            'actual_state',
            'result',
            'verified_at',
            'details',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


class RepairPlanSerializer(serializers.ModelSerializer):
    """
    Serializer for RepairPlan model.
    Includes nested employee summary, violation details, execution logs, and verifications.
    """
    employee_detail = EmployeeSerializer(source='employee', read_only=True)
    violation_detail = IntegrityViolationSerializer(source='violation', read_only=True)
    sensitivity_level = serializers.ReadOnlyField()
    latest_execution_log = serializers.SerializerMethodField()
    latest_verification = serializers.SerializerMethodField()

    class Meta:
        model = RepairPlan
        fields = [
            'id',
            'employee',
            'employee_detail',
            'violation',
            'violation_detail',
            'target_system',
            'action',
            'reason',
            'risk_level',
            'sensitivity_level',
            'status',
            'latest_execution_log',
            'latest_verification',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'sensitivity_level',
        ]

    def get_latest_execution_log(self, obj):
        latest = obj.execution_logs.order_by('-started_at').first()
        if latest:
            return RepairExecutionLogSerializer(latest).data
        return None

    def get_latest_verification(self, obj):
        latest = obj.verifications.order_by('-created_at').first()
        if latest:
            return RepairVerificationSerializer(latest).data
        return None
