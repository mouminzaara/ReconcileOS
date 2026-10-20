"""
Comprehensive Tests for Repair Plan Generation API Contract and Validation (Phase 2C).

Tests:
1. Valid employee_id succeeds with HTTP 200 and generated plans.
2. Missing employee_id (empty payload or null) returns HTTP 400.
3. Sending 'email' instead of 'employee_id' returns HTTP 400 (rejection of mismatched contract).
4. Malformed/invalid employee_id UUID returns HTTP 400.
5. Non-existent employee_id returns HTTP 404.
6. Role-based permission enforcement: Anonymous (401), VIEWER (403), OPERATOR (200), ADMIN (200).
"""

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from apps.employees.models import Employee, EmployeeStatus
from apps.connectors.models import VPNAccess, VPNAccessStatus
from apps.rules.models import Rule, RuleSeverity
from apps.accounts.models import UserProfile, UserRole
from apps.reconciliation.engine import ReconciliationEngine
from apps.reconciliation.models import IntegrityViolation, ViolationStatus


class RepairPlanGenerateAPITestCase(TestCase):
    """
    Test suite for POST /api/v1/workflows/plans/generate/ API contract and validation.
    """

    def setUp(self):
        self.client = APIClient()

        # Users
        self.admin_user = User.objects.create_user('admin_api', 'admin@example.com', 'password123')
        UserProfile.objects.create(user=self.admin_user, role=UserRole.ADMIN)

        self.operator_user = User.objects.create_user('operator_api', 'operator@example.com', 'password123')
        UserProfile.objects.create(user=self.operator_user, role=UserRole.OPERATOR)

        self.viewer_user = User.objects.create_user('viewer_api', 'viewer@example.com', 'password123')
        UserProfile.objects.create(user=self.viewer_user, role=UserRole.VIEWER)

        # Invariant Rule
        self.rule = Rule.objects.create(
            rule_code='INV-TEST-001',
            name='Terminated Employee Revocation',
            description='Terminated employees must have VPN access disabled',
            source_system='HR',
            condition_attribute='status',
            condition_value='TERMINATED',
            target_system='VPN',
            expected_attribute='status',
            expected_value='DISABLED',
            severity=RuleSeverity.CRITICAL,
            is_enabled=True
        )

        # Employee with drift
        self.employee = Employee.objects.create(
            full_name='Vikram Malhotra',
            email='vikram@company.com',
            department='Engineering',
            status=EmployeeStatus.TERMINATED
        )
        self.vpn_access = VPNAccess.objects.create(
            employee=self.employee,
            status=VPNAccessStatus.ENABLED
        )

        # Detect violation
        engine = ReconciliationEngine()
        engine.evaluate_employee_rules(str(self.employee.id))
        self.violation = IntegrityViolation.objects.get(employee=self.employee, status=ViolationStatus.OPEN)

        self.generate_url = '/api/v1/workflows/plans/generate/'

    def test_valid_employee_id_generates_plan(self):
        """A valid employee_id generates repair plans and returns HTTP 200."""
        self.client.force_authenticate(user=self.operator_user)

        response = self.client.post(self.generate_url, {'employee_id': str(self.employee.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['action'], 'DISABLE VPN ACCESS')

    def test_missing_employee_id_returns_400(self):
        """Omitting employee_id returns HTTP 400 with a clear error message."""
        self.client.force_authenticate(user=self.operator_user)

        response = self.client.post(self.generate_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 'error')
        self.assertIn("Missing required parameter 'employee_id'", response.data['message'])

    def test_sending_email_instead_of_employee_id_rejected(self):
        """Sending 'email' (the old frontend bug) is rejected with HTTP 400."""
        self.client.force_authenticate(user=self.operator_user)

        response = self.client.post(self.generate_url, {'email': self.employee.email})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 'error')
        self.assertIn("Missing required parameter 'employee_id'", response.data['message'])

    def test_invalid_uuid_format_returns_400(self):
        """A malformed UUID format returns HTTP 400 Bad Request."""
        self.client.force_authenticate(user=self.operator_user)

        response = self.client.post(self.generate_url, {'employee_id': 'not-a-valid-uuid'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 'error')
        self.assertIn("Invalid employee_id format", response.data['message'])

    def test_non_existent_employee_id_returns_404(self):
        """A valid UUID that does not correspond to an existing Employee returns HTTP 404."""
        self.client.force_authenticate(user=self.operator_user)

        import uuid
        fake_uuid = str(uuid.uuid4())
        response = self.client.post(self.generate_url, {'employee_id': fake_uuid})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['status'], 'error')
        self.assertIn("not found", response.data['message'])

    def test_generate_plans_rbac_permissions(self):
        """
        Verify RBAC permissions on generate_plans endpoint:
        - Anonymous: 401 Unauthorized
        - VIEWER: 403 Forbidden
        - OPERATOR: 200 OK
        - ADMIN: 200 OK
        """
        payload = {'employee_id': str(self.employee.id)}

        # 1. Anonymous
        self.client.logout()
        resp = self.client.post(self.generate_url, payload)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # 2. VIEWER
        self.client.force_authenticate(user=self.viewer_user)
        resp = self.client.post(self.generate_url, payload)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # 3. OPERATOR
        self.client.force_authenticate(user=self.operator_user)
        resp = self.client.post(self.generate_url, payload)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # 4. ADMIN
        self.client.force_authenticate(user=self.admin_user)
        resp = self.client.post(self.generate_url, payload)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
