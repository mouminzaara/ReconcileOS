"""
Unit tests for ReconcileOS Human-in-the-Loop Approvals Engine (Milestone 8).
"""

from django.test import TestCase
from django.core.management import call_command
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from io import StringIO

from apps.employees.models import Employee, EmployeeStatus
from apps.connectors.models import VPNAccess, VPNAccessStatus
from apps.rules.models import Rule, RuleSeverity
from apps.accounts.models import UserProfile, UserRole
from apps.reconciliation.models import IntegrityViolation, ViolationStatus
from apps.reconciliation.engine import ReconciliationEngine
from apps.workflows.models import RepairPlan, PlanStatus
from apps.workflows.planner import RepairPlanner
from apps.approvals.models import ApprovalRequest, ApprovalDecision
from apps.approvals.services import ApprovalService


class ApprovalsTestCase(TestCase):
    """
    Test suite for Human-in-the-Loop Approvals models, services, state machine, and API endpoints.
    """

    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser('admin_appr', 'admin@appr.com', 'admin123')
        UserProfile.objects.create(user=self.admin_user, role=UserRole.ADMIN)

        self.rule = Rule.objects.create(
            rule_code='INV-RULE-001',
            name='Terminated Employee Access Revocation',
            description='Terminated employees must have all downstream VPN access disabled.',
            source_system='HR',
            condition_attribute='status',
            condition_value='TERMINATED',
            target_system='VPN',
            expected_attribute='status',
            expected_value='DISABLED',
            severity=RuleSeverity.CRITICAL,
            is_enabled=True
        )

        self.employee = Employee.objects.create(
            full_name='Rahul Kumar',
            email='rahul.kumar@company.com',
            department='Engineering',
            status=EmployeeStatus.TERMINATED
        )

        self.vpn_access = VPNAccess.objects.create(
            employee=self.employee,
            status=VPNAccessStatus.ENABLED
        )

        self.engine = ReconciliationEngine()
        self.engine.evaluate_employee_rules(str(self.employee.id))
        self.violation = IntegrityViolation.objects.get(employee=self.employee, status=ViolationStatus.OPEN)

        self.planner = RepairPlanner()
        self.plan, _ = self.planner.plan_for_violation(self.violation)

        self.approval_request = ApprovalRequest.objects.get(repair_plan=self.plan)

    def test_approval_request_auto_created_in_pending_state(self):
        """
        Verify that creating a RepairPlan automatically creates an ApprovalRequest in PENDING state.
        """
        self.assertIsNotNone(self.approval_request)
        self.assertEqual(self.approval_request.decision, ApprovalDecision.PENDING)
        self.assertTrue(self.approval_request.is_pending)
        self.assertEqual(self.plan.status, PlanStatus.PENDING)

    def test_approve_repair_plan_transition(self):
        """
        Verify that approving an ApprovalRequest transitions decision to APPROVED
        and updates RepairPlan.status to APPROVED (eligible for execution).
        """
        ApprovalService.approve_request(self.approval_request, comment="Approved by Admin")

        self.approval_request.refresh_from_db()
        self.plan.refresh_from_db()

        self.assertEqual(self.approval_request.decision, ApprovalDecision.APPROVED)
        self.assertEqual(self.approval_request.comment, "Approved by Admin")
        self.assertIsNotNone(self.approval_request.decided_at)

        self.assertEqual(self.plan.status, PlanStatus.APPROVED)

    def test_reject_repair_plan_transition(self):
        """
        Verify that rejecting an ApprovalRequest transitions decision to REJECTED
        and updates RepairPlan.status to REJECTED.
        """
        ApprovalService.reject_request(self.approval_request, comment="Security policy waiver")

        self.approval_request.refresh_from_db()
        self.plan.refresh_from_db()

        self.assertEqual(self.approval_request.decision, ApprovalDecision.REJECTED)
        self.assertEqual(self.approval_request.comment, "Security policy waiver")
        self.assertEqual(self.plan.status, PlanStatus.REJECTED)

    def test_prevent_invalid_state_transitions(self):
        """
        Verify that invalid state transitions raise ValidationError.
        """
        ApprovalService.approve_request(self.approval_request)

        with self.assertRaises(ValidationError):
            ApprovalService.approve_request(self.approval_request)

        with self.assertRaises(ValidationError):
            ApprovalService.reject_request(self.approval_request)

    def test_vpn_access_remains_enabled_after_approval(self):
        """
        Verify that approving a repair plan does NOT execute repair actions
        and VPN access remains ENABLED.
        """
        ApprovalService.approve_request(self.approval_request)

        self.vpn_access.refresh_from_db()
        self.plan.refresh_from_db()
        self.assertEqual(self.vpn_access.status, VPNAccessStatus.ENABLED)
        self.assertEqual(self.plan.status, PlanStatus.APPROVED)

    def test_approve_repair_management_command(self):
        """
        Test management command to view and approve repair plans via CLI.
        """
        out = StringIO()
        call_command('approve_repair', '--plan-id', str(self.plan.id), '--action', 'approve', '--comment', 'CLI Approval', stdout=out)
        output = out.getvalue()

        self.assertIn("[APPROVED]", output)
        self.plan.refresh_from_db()
        self.assertEqual(self.plan.status, PlanStatus.APPROVED)

    def test_approvals_api_pending_list_approve_reject(self):
        """
        Test REST API endpoints for viewing pending approvals, approving, and rejecting.
        """
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get('/api/v1/approvals/pending/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        approve_url = f"/api/v1/approvals/{self.approval_request.id}/approve/"
        response = self.client.post(approve_url, {'comment': 'API approved'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')

        response = self.client.post(approve_url, {'comment': 'Duplicate approve'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 'error')
