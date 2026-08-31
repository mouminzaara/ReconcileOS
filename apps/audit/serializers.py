"""
Serializers for Audit Log REST API.
"""

from rest_framework import serializers
from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_email = serializers.CharField(source='employee.email', read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'id',
            'timestamp',
            'actor',
            'event_type',
            'employee',
            'employee_name',
            'employee_email',
            'system',
            'action',
            'previous_state',
            'new_state',
            'result',
            'correlation_id',
            'additional_metadata',
            'previous_hash',
            'current_hash',
        ]
        read_only_fields = fields
