"""
Automated unit tests for Authentication and Role-Based Access Control (Milestone 17).
"""

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import UserProfile, UserRole
from apps.employees.models import Employee, EmployeeStatus
from apps.connectors.models import VPNAccess, VPNAccessStatus
from apps.rules.models import Rule, RuleSeverity
from apps.reconciliation.models import IntegrityViolation, ViolationStatus
from apps.workflows.models import RepairPlan, PlanStatus
from apps.approvals.models import ApprovalRequest, ApprovalDecision


class RBACTestCase(TestCase):
    """
    Test suite for SimpleJWT authentication and RBAC permissions:
    - 401 Unauthorized for unauthenticated API requests
    - 403 Forbidden for VIEWER attempting repair approvals or execution
    - 200 OK for OPERATOR running reconciliation audit
    - 200 OK for ADMIN approving repairs and executing self-healing plans
    """

    def setUp(self):
        self.client = APIClient()

        # 1. Create Users with Profiles
        self.admin_user = User.objects.create_user('admin_test', 'admin@test.com', 'admin123')
        UserProfile.objects.create(user=self.admin_user, role=UserRole.ADMIN)

        self.operator_user = User.objects.create_user('operator_test', 'operator@test.com', 'operator123')
        UserProfile.objects.create(user=self.operator_user, role=UserRole.OPERATOR)

        self.viewer_user = User.objects.create_user('viewer_test', 'viewer@test.com', 'viewer123')
        UserProfile.objects.create(user=self.viewer_user, role=UserRole.VIEWER)

        # 2. Create Domain Data (Employee, Rule, Violation, RepairPlan, Approval)
        self.rule = Rule.objects.create(
            rule_code='INV-RULE-001', name='VPN Rule', source_system='HR',
            condition_attribute='status', condition_value='TERMINATED',
            target_system='VPN', expected_attribute='status', expected_value='DISABLED',
            severity=RuleSeverity.CRITICAL, is_enabled=True
        )
        self.employee = Employee.objects.create(
            full_name='Rahul Kumar', email='rahul.kumar@test.com',
            department='Engineering', status=EmployeeStatus.TERMINATED
        )
        self.vpn_access = VPNAccess.objects.create(employee=self.employee, status=VPNAccessStatus.ENABLED)
        self.violation = IntegrityViolation.objects.create(
            employee=self.employee, rule=self.rule, affected_system='VPN',
            expected_state='DISABLED', actual_state='ENABLED', status=ViolationStatus.OPEN
        )
        self.repair_plan = RepairPlan.objects.create(
            employee=self.employee, violation=self.violation, target_system='VPN',
            action='DISABLE VPN ACCESS', reason='HR is TERMINATED', risk_level='CRITICAL',
            status=PlanStatus.APPROVED
        )
        self.approval_request = ApprovalRequest.objects.create(
            repair_plan=self.repair_plan, decision=ApprovalDecision.APPROVED
        )

    def _login(self, user):
        res = self.client.post('/api/v1/auth/login/', {'username': user.username, 'password': user.username.split('_')[0] + '123'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        token = res.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_unauthenticated_request_rejected(self):
        """
        Verify unauthenticated API requests return 401 Unauthorized.
        """
        self.client.credentials()  # Clear auth
        res = self.client.get('/api/v1/employees/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_viewer_access_and_restrictions(self):
        """
        Verify VIEWER role can read data but is denied (403 Forbidden) on write & approval actions.
        """
        self._login(self.viewer_user)

        # Allowed: GET Dashboard / Violations
        res_get = self.client.get('/api/v1/reconciliation/violations/')
        self.assertEqual(res_get.status_code, status.HTTP_200_OK)

        # Denied: POST Approve Repair (Requires ADMIN)
        res_approve = self.client.post(f'/api/v1/approvals/{self.approval_request.id}/approve/')
        self.assertEqual(res_approve.status_code, status.HTTP_403_FORBIDDEN)

        # Denied: POST Execute Repair (Requires ADMIN)
        res_exec = self.client.post(f'/api/v1/workflows/plans/{self.repair_plan.id}/execute/')
        self.assertEqual(res_exec.status_code, status.HTTP_403_FORBIDDEN)

    def test_operator_access_and_restrictions(self):
        """
        Verify OPERATOR role can trigger reconciliation scans but is denied (403 Forbidden) on repair execution.
        """
        self._login(self.operator_user)

        # Allowed: Run Reconciliation Audit
        res_audit = self.client.post('/api/v1/reconciliation/run/')
        self.assertEqual(res_audit.status_code, status.HTTP_200_OK)

        # Denied: Execute Repair Plan (Requires ADMIN)
        res_exec = self.client.post(f'/api/v1/workflows/plans/{self.repair_plan.id}/execute/')
        self.assertEqual(res_exec.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_full_access(self):
        """
        Verify ADMIN role can execute repair plans and perform sensitive operations.
        """
        self._login(self.admin_user)

        # Allowed: Execute Repair Plan
        res_exec = self.client.post(f'/api/v1/workflows/plans/{self.repair_plan.id}/execute/')
        self.assertEqual(res_exec.status_code, status.HTTP_200_OK)
        self.assertEqual(res_exec.data['status'], 'success')
