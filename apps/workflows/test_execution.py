"""
Automated unit tests for ReconcileOS Repair Execution Engine (Milestone 9).
"""

from django.test import TestCase
from django.core.management import call_command
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
from apps.workflows.models import RepairPlan, PlanStatus, ExecutionStatus
from apps.workflows.planner import RepairPlanner
from apps.workflows.executor import RepairExecutor, IneligiblePlanExecutionException, ExecutionException
from apps.approvals.models import ApprovalRequest, ApprovalDecision
from apps.approvals.services import ApprovalService


class RepairExecutionTestCase(TestCase):
    """
    Test suite for Repair Execution Engine.
    """

    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser('admin_exec', 'admin@exec.com', 'admin123')
        UserProfile.objects.create(user=self.admin_user, role=UserRole.ADMIN)
        self.client.force_authenticate(user=self.admin_user)

        self.rule = Rule.objects.create(
            rule_code='INV-RULE-001',
            name='Terminated Employee Access Revocation',
            description='Terminated employees must not have VPN access.',
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
        self.executor = RepairExecutor()

    def test_unapproved_repair_cannot_execute(self):
        """
        Verify that a PENDING (unapproved) repair plan cannot be executed.
        """
        self.assertEqual(self.plan.status, PlanStatus.PENDING)
        with self.assertRaises(IneligiblePlanExecutionException):
            self.executor.execute_plan(self.plan)

        self.vpn_access.refresh_from_db()
        self.assertEqual(self.vpn_access.status, VPNAccessStatus.ENABLED)

    def test_rejected_repair_cannot_execute(self):
        """
        Verify that a REJECTED repair plan cannot be executed.
        """
        ApprovalService.reject_request(self.approval_request, comment="Waiver granted")
        self.plan.refresh_from_db()
        self.assertEqual(self.plan.status, PlanStatus.REJECTED)

        with self.assertRaises(IneligiblePlanExecutionException):
            self.executor.execute_plan(self.plan)

        self.vpn_access.refresh_from_db()
        self.assertEqual(self.vpn_access.status, VPNAccessStatus.ENABLED)

    def test_successful_repair_execution_and_vpn_state_change(self):
        """
        Verify that an APPROVED repair plan executes successfully via the VPN connector.
        """
        ApprovalService.approve_request(self.approval_request, comment="Approved for remediation")
        self.plan.refresh_from_db()
        self.assertEqual(self.plan.status, PlanStatus.APPROVED)

        log = self.executor.execute_plan(self.plan)

        self.plan.refresh_from_db()
        self.vpn_access.refresh_from_db()

        self.assertEqual(log.status, ExecutionStatus.SUCCESS)
        self.assertIn(self.plan.status, [PlanStatus.SUCCESS, PlanStatus.COMPLETED])
        self.assertIn("Successfully disabled VPN access", log.output_message)

        self.assertEqual(self.vpn_access.status, VPNAccessStatus.DISABLED)

    def test_execute_repair_management_command(self):
        """
        Test execution via execute_repair management command.
        """
        ApprovalService.approve_request(self.approval_request)

        out = StringIO()
        call_command('execute_repair', '--plan-id', str(self.plan.id), stdout=out)
        output = out.getvalue()

        self.assertIn("[EXECUTION SUCCESS]", output)

        self.vpn_access.refresh_from_db()
        self.assertEqual(self.vpn_access.status, VPNAccessStatus.DISABLED)

    def test_execute_repair_api_endpoint(self):
        """
        Test API endpoint POST /api/v1/workflows/plans/<id>/execute/.
        """
        ApprovalService.approve_request(self.approval_request)

        execute_url = f"/api/v1/workflows/plans/{self.plan.id}/execute/"
        response = self.client.post(execute_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn(response.data['plan_status'], ['SUCCESS', 'COMPLETED'])

        self.vpn_access.refresh_from_db()
        self.assertEqual(self.vpn_access.status, VPNAccessStatus.DISABLED)

    def test_unsupported_connector_failure_handling(self):
        """
        Verify that targeting an unknown system handles errors cleanly without corrupting state.
        """
        ApprovalService.approve_request(self.approval_request)
        self.plan.refresh_from_db()
        self.plan.target_system = 'UNKNOWN_SYSTEM'
        self.plan.save()

        with self.assertRaises(ExecutionException):
            self.executor.execute_plan(self.plan)

        self.plan.refresh_from_db()
        self.assertEqual(self.plan.status, PlanStatus.FAILED)
