"""
Serializers for Employee API endpoints.
"""

from rest_framework import serializers
from .models import Employee, EmployeeStatus


class EmployeeSerializer(serializers.ModelSerializer):
    """
    Serializer for standard Employee CRUD operations.
    """
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )

    class Meta:
        model = Employee
        fields = [
            'id',
            'full_name',
            'email',
            'department',
            'status',
            'status_display',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_email(self, value):
        """
        Normalize email to lowercase and strip whitespace.
        Ensure uniqueness case-insensitively.
        """
        cleaned_email = value.strip().lower()
        query = Employee.objects.filter(email__iexact=cleaned_email)
        if self.instance:
            query = query.exclude(pk=self.instance.pk)
        if query.exists():
            raise serializers.ValidationError("An employee with this email address already exists.")
        return cleaned_email

    def validate_full_name(self, value):
        """
        Ensure full_name is non-empty after stripping whitespace.
        """
        cleaned_name = value.strip()
        if not cleaned_name:
            raise serializers.ValidationError("Full name cannot be empty or just whitespace.")
        return cleaned_name

    def validate_department(self, value):
        """
        Ensure department is non-empty after stripping whitespace.
        """
        cleaned_dept = value.strip()
        if not cleaned_dept:
            raise serializers.ValidationError("Department cannot be empty or just whitespace.")
        return cleaned_dept


class EmployeeTerminateSerializer(serializers.Serializer):
    """
    Serializer for the explicit termination action endpoint.
    Accepts an optional termination reason / note for auditability.
    """
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,
        help_text="Optional reason for termination (for audit tracking)."
    )
