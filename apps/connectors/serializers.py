"""
Serializers for Simulated VPN Connector API endpoints.
"""

from rest_framework import serializers
from .models import VPNAccess, VPNAccessStatus


class VPNAccessSerializer(serializers.ModelSerializer):
    """
    Serializer for VPNAccess records with enriched Employee context.
    """
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    employee_id = serializers.UUIDField(
        source='employee.id',
        read_only=True
    )
    employee_email = serializers.EmailField(
        source='employee.email',
        read_only=True
    )
    employee_name = serializers.CharField(
        source='employee.full_name',
        read_only=True
    )
    employee_department = serializers.CharField(
        source='employee.department',
        read_only=True
    )
    employee_status = serializers.CharField(
        source='employee.status',
        read_only=True
    )

    class Meta:
        model = VPNAccess
        fields = [
            'id',
            'employee',
            'employee_id',
            'employee_email',
            'employee_name',
            'employee_department',
            'employee_status',
            'status',
            'status_display',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'employee_id',
            'employee_email',
            'employee_name',
            'employee_department',
            'employee_status',
            'status_display',
            'created_at',
            'updated_at',
        ]


class VPNActionResponseSerializer(serializers.Serializer):
    """
    Standard schema for VPN enable / disable action responses.
    """
    status = serializers.CharField()
    message = serializers.CharField()
    status_changed = serializers.BooleanField()
    action = serializers.CharField()
    vpn_access = VPNAccessSerializer()
