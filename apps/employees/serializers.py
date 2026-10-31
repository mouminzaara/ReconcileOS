"""
Serializers for Employee API endpoints.
"""

from rest_framework import serializers
from .models import Employee, EmployeeStatus


class EmployeeSerializer(serializers.ModelSerializer):
    """
    Serializer for standard Employee CRUD operations.
    Exposes authentic connected downstream systems and detailed connection state.
    """
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    systems_connected = serializers.SerializerMethodField()
    connected_systems = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            'id',
            'full_name',
            'email',
            'department',
            'status',
            'status_display',
            'systems_connected',
            'connected_systems',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_connected_systems(self, obj) -> list:
        """
        Derives comprehensive per-system status based on actual downstream connector models.
        Distinguishes active connected, confirmed disconnected/revoked, and not provisioned.
        """
        systems = [
            {
                "key": "hr",
                "system": "HR",
                "name": "HR Directory",
                "status": obj.status,
                "is_connected": obj.status == EmployeeStatus.ACTIVE,
                "state": "CONNECTED" if obj.status == EmployeeStatus.ACTIVE else "TERMINATED",
                "details": f"HR Status: {obj.status}"
            }
        ]

        # 1. VPN Access
        try:
            vpn = getattr(obj, 'vpn_access', None)
            if vpn:
                is_conn = (vpn.status == 'ENABLED')
                systems.append({
                    "key": "vpn",
                    "system": "VPN",
                    "name": "Enterprise VPN Gateway",
                    "status": vpn.status,
                    "is_connected": is_conn,
                    "state": "CONNECTED" if is_conn else "DISCONNECTED",
                    "details": f"VPN Access: {vpn.status}"
                })
        except Exception:
            pass

        # 2. GitHub Membership
        try:
            gh = getattr(obj, 'github_membership', None)
            if gh:
                is_conn = (gh.status == 'MEMBER')
                systems.append({
                    "key": "github",
                    "system": "GitHub",
                    "name": "GitHub Enterprise",
                    "status": gh.status,
                    "is_connected": is_conn,
                    "state": "CONNECTED" if is_conn else "DISCONNECTED",
                    "details": f"Org Membership: {gh.status} ({gh.github_username})"
                })
        except Exception:
            pass

        # 3. Cloud IAM
        try:
            cloud = getattr(obj, 'cloud_access', None)
            if cloud:
                is_conn = cloud.role in ['DEVELOPER_ROLE', 'ADMIN_ROLE']
                is_revoked = cloud.role in ['REVOKED', 'NO_ROLE']
                systems.append({
                    "key": "cloud",
                    "system": "Cloud IAM",
                    "name": "Cloud IAM (AWS)",
                    "status": cloud.role,
                    "is_connected": is_conn,
                    "state": "CONNECTED" if is_conn else ("DISCONNECTED" if is_revoked else "UNKNOWN"),
                    "details": f"Cloud Role: {cloud.role}"
                })
        except Exception:
            pass

        # 4. Slack Account
        try:
            slack = getattr(obj, 'slack_account', None)
            if slack:
                is_conn = (slack.status == 'ACTIVE')
                systems.append({
                    "key": "slack",
                    "system": "Slack",
                    "name": "Slack Workspace",
                    "status": slack.status,
                    "is_connected": is_conn,
                    "state": "CONNECTED" if is_conn else "DISCONNECTED",
                    "details": f"Slack Account: {slack.status}"
                })
        except Exception:
            pass

        return systems

    def get_systems_connected(self, obj) -> list:
        """
        Returns list of system name strings for actively connected systems.
        """
        detailed = self.get_connected_systems(obj)
        return [s["system"] for s in detailed if s.get("is_connected")]

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
