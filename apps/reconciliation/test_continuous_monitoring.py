"""
Automated unit tests for ReconcileOS Continuous Integrity Monitoring Engine & Mandatory Human Approval.
"""

from io import StringIO
from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from apps.employees.models import Employee, EmployeeStatus
from apps.connectors.models import VPNAccess, VPNAccessStatus
from apps.rules.models import Rule, RuleSeverity
from apps.accounts.models import UserProfile, UserRole
from apps.reconciliation.models import IntegrityViolation, ViolationStatus
from apps.reconciliation.monitor import ContinuousMonitor
from apps.workflows.models import RepairPlan, PlanStatus, RepairVerification, VerificationResult
from apps.workflows.executor import RepairExecutor, IneligiblePlanExecutionException
from apps.approvals.models import ApprovalRequest, ApprovalDecision
from apps.approvals.services import ApprovalService


class ContinuousIntegrityMonitoringTestCase(TestCase):
    """
    Test suite for Continuous Integrity Monitoring Engine and Mandatory Human-in-the-Loop Governance.
    """

    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser('admin_mon', 'admin@mon.com', 'admin123')
        UserProfile.objects.create(user=self.admin_user, role=UserRole.ADMIN)

        self.operator_user = User.objects.create_user('operator_mon', 'operator@mon.com', 'operator123')
        UserProfile.objects.create(user=self.operator_user, role=UserRole.OPERATOR)

        self.viewer_user = User.objects.create_user('viewer_mon', 'viewer@mon.com', 'viewer123')
        UserProfile.objects.create(user=self.viewer_user, role=UserRole.VIEWER)

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
            status=VPNAccessStatus.DISABLED
        )

        self.monitor = ContinuousMonitor()

    def test_initial_state_is_consistent(self):
        """
        Verify that when employee is TERMINATED and VPN is DISABLED, the initial monitoring cycle yields CONSISTENT.
        """
        summary = self.monitor.run_monitoring_cycle(employee_id=str(self.employee.id))
        self.assertEqual(summary['system_status'], 'CONSISTENT')
        self.assertEqual(summary['remaining_open_violations_count'], 0)
        self.assertEqual(summary['repair_plans_generated_count'], 0)
        self.assertEqual(summary['repairs_executed_count'], 0)

    def test_monitoring_detects_drift_without_silent_approval(self):
        """
        Prove that monitoring detects drift and generates repair plans in PENDING state
        without silently approving or executing them.
        """
        # Create authorization drift: Employee TERMINATED, VPN re-enabled
        self.vpn_access.enable()
        self.vpn_access.refresh_from_db()
        self.assertEqual(self.vpn_access.status, VPNAccessStatus.ENABLED)

        # Execute monitoring cycle
        summary = self.monitor.run_monitoring_cycle(employee_id=str(self.employee.id))

        # Drift must be detected and repair plan generated
        self.assertEqual(summary['violations_detected_count'], 1)
        self.assertEqual(summary['repair_plans_generated_count'], 1)

        # Mandatory human approval rule: approvals_processed_count and repairs_executed_count MUST be 0
        self.assertEqual(summary['approvals_processed_count'], 0)
        self.assertEqual(summary['repairs_executed_count'], 0)
        self.assertEqual(summary['remaining_open_violations_count'], 1)
        self.assertEqual(summary['system_status'], 'DRIFT_DETECTED')

        # Verify underlying plan and approval request remain strictly PENDING
        violation = IntegrityViolation.objects.get(employee=self.employee, affected_system='VPN')
        self.assertEqual(violation.status, ViolationStatus.OPEN)

        plan = RepairPlan.objects.get(violation=violation)
        self.assertEqual(plan.status, PlanStatus.PENDING)

        approval_req = ApprovalRequest.objects.get(repair_plan=plan)
        self.assertEqual(approval_req.decision, ApprovalDecision.PENDING)

        # Downstream VPN state must NOT have been mutated
        self.vpn_access.refresh_from_db()
        self.assertEqual(self.vpn_access.status, VPNAccessStatus.ENABLED)

    def test_pending_plan_cannot_execute(self):
        """
        Prove that a PENDING (unapproved) repair plan cannot execute.
        """
        self.vpn_access.enable()
        self.monitor.run_monitoring_cycle(employee_id=str(self.employee.id))

        plan = RepairPlan.objects.get(employee=self.employee)
        self.assertEqual(plan.status, PlanStatus.PENDING)

        executor = RepairExecutor()
        with self.assertRaises(IneligiblePlanExecutionException):
            executor.execute_plan(plan, executed_by=self.admin_user)

        # Downstream state must remain unmutated
        self.vpn_access.refresh_from_db()
        self.assertEqual(self.vpn_access.status, VPNAccessStatus.ENABLED)

    def test_rejected_plan_cannot_execute(self):
        """
        Prove that a REJECTED repair plan cannot execute.
        """
        self.vpn_access.enable()
        self.monitor.run_monitoring_cycle(employee_id=str(self.employee.id))

        plan = RepairPlan.objects.get(employee=self.employee)
        approval_req = ApprovalRequest.objects.get(repair_plan=plan)

        # Reject the approval request
        ApprovalService.reject_request(approval_req, decided_by=self.admin_user, comment="Rejected by SecOps")
        plan.refresh_from_db()
        self.assertEqual(plan.status, PlanStatus.REJECTED)

        executor = RepairExecutor()
        with self.assertRaises(IneligiblePlanExecutionException):
            executor.execute_plan(plan, executed_by=self.admin_user)

        # Downstream state must remain unmutated
        self.vpn_access.refresh_from_db()
        self.assertEqual(self.vpn_access.status, VPNAccessStatus.ENABLED)

    def test_validly_approved_plan_can_execute_under_intended_permissions(self):
        """
        Prove the complete governance lifecycle:
        1. Drift detected -> Plan created (PENDING).
        2. Admin approves plan -> Plan APPROVED.
        3. Admin executes plan -> Plan COMPLETED, VPN DISABLED, Violation RESOLVED.
        4. Subsequent monitoring confirms CONSISTENT.
        """
        self.vpn_access.enable()
        summary = self.monitor.run_monitoring_cycle(employee_id=str(self.employee.id))
        self.assertEqual(summary['system_status'], 'DRIFT_DETECTED')

        plan = RepairPlan.objects.get(employee=self.employee)
        approval_req = ApprovalRequest.objects.get(repair_plan=plan)

        # 1. Admin Human Approval
        ApprovalService.approve_request(
            approval_req,
            decided_by=self.admin_user,
            comment="Approved offboarding remediation"
        )
        plan.refresh_from_db()
        self.assertEqual(plan.status, PlanStatus.APPROVED)

        # 2. Execution by authorized administrator
        executor = RepairExecutor()
        log = executor.execute_plan(plan, executed_by=self.admin_user)
        self.assertEqual(log.status, 'SUCCESS')

        # 3. Verify state and verification records
        self.vpn_access.refresh_from_db()
        self.assertEqual(self.vpn_access.status, VPNAccessStatus.DISABLED)

        plan.refresh_from_db()
        self.assertEqual(plan.status, PlanStatus.COMPLETED)

        violation = IntegrityViolation.objects.get(employee=self.employee, affected_system='VPN')
        self.assertEqual(violation.status, ViolationStatus.RESOLVED)

        verification = RepairVerification.objects.get(repair_plan=plan)
        self.assertEqual(verification.result, VerificationResult.VERIFIED)

        # 4. Subsequent monitoring confirms system is consistent
        final_summary = self.monitor.run_monitoring_cycle(employee_id=str(self.employee.id))
        self.assertEqual(final_summary['system_status'], 'CONSISTENT')
        self.assertEqual(final_summary['remaining_open_violations_count'], 0)

    def test_monitoring_disallows_auto_approve_policy(self):
        """
        Prove that passing auto_approve_policy=True to run_monitoring_cycle raises ValueError.
        """
        self.vpn_access.enable()
        with self.assertRaises(ValueError) as ctx:
            self.monitor.run_monitoring_cycle(
                employee_id=str(self.employee.id),
                auto_approve_policy=True
            )
        self.assertIn("Automatic approval is disabled by governance policy", str(ctx.exception))

    def test_api_rejects_auto_approve_bypass(self):
        """
        Prove that calling POST /api/v1/reconciliation/monitor/ with auto_approve=true
        fails safely with HTTP 400 Bad Request, preventing bypass of human approval.
        """
        self.vpn_access.enable()
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post("/api/v1/reconciliation/monitor/", {
            "employee_id": str(self.employee.id),
            "auto_approve": True
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 'error')
        self.assertIn("Automatic approval is disabled by governance policy", response.data['message'])

        # VPN must remain ENABLED (no mutation occurred)
        self.vpn_access.refresh_from_db()
        self.assertEqual(self.vpn_access.status, VPNAccessStatus.ENABLED)

    def test_api_runs_normal_monitoring_without_auto_approve(self):
        """
        Prove that calling POST /api/v1/reconciliation/monitor/ without auto_approve
        runs normal drift detection and generates pending plans without executing them.
        """
        self.vpn_access.enable()
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post("/api/v1/reconciliation/monitor/", {
            "employee_id": str(self.employee.id)
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['system_status'], 'DRIFT_DETECTED')
        self.assertEqual(response.data['violations_detected_count'], 1)
        self.assertEqual(response.data['repair_plans_generated_count'], 1)
        self.assertEqual(response.data['approvals_processed_count'], 0)
        self.assertEqual(response.data['repairs_executed_count'], 0)

        # Plan must be PENDING
        plan = RepairPlan.objects.get(employee=self.employee)
        self.assertEqual(plan.status, PlanStatus.PENDING)

        # VPN must remain ENABLED
        self.vpn_access.refresh_from_db()
        self.assertEqual(self.vpn_access.status, VPNAccessStatus.ENABLED)

    def test_api_requires_operator_or_admin_role(self):
        """
        Prove that monitoring endpoint enforces RBAC:
        - Anonymous user: 401 Unauthorized
        - Viewer user: 403 Forbidden
        - Operator user: 200 OK
        - Admin user: 200 OK
        """
        url = "/api/v1/reconciliation/monitor/"

        # Anonymous
        res_anon = self.client.post(url, {}, format='json')
        self.assertEqual(res_anon.status_code, status.HTTP_401_UNAUTHORIZED)

        # Viewer
        self.client.force_authenticate(user=self.viewer_user)
        res_viewer = self.client.post(url, {}, format='json')
        self.assertEqual(res_viewer.status_code, status.HTTP_403_FORBIDDEN)

        # Operator
        self.client.force_authenticate(user=self.operator_user)
        res_operator = self.client.post(url, {}, format='json')
        self.assertEqual(res_operator.status_code, status.HTTP_200_OK)

        # Admin
        self.client.force_authenticate(user=self.admin_user)
        res_admin = self.client.post(url, {}, format='json')
        self.assertEqual(res_admin.status_code, status.HTTP_200_OK)

    def test_management_command_rejects_auto_approve(self):
        """
        Prove that running `manage.py run_continuous_monitor --auto-approve` fails safely with CommandError.
        """
        self.vpn_access.enable()
        with self.assertRaises(CommandError) as ctx:
            call_command(
                'run_continuous_monitor',
                '--once',
                '--employee-id', str(self.employee.id),
                '--auto-approve'
            )
        self.assertIn("--auto-approve is disabled by governance policy", str(ctx.exception))

    def test_management_command_runs_normal_monitoring(self):
        """
        Prove that running `manage.py run_continuous_monitor` without `--auto-approve`
        detects drift, generates pending plans, and does not silently approve them.
        """
        self.vpn_access.enable()
        out = StringIO()
        call_command(
            'run_continuous_monitor',
            '--once',
            '--employee-id', str(self.employee.id),
            stdout=out
        )
        output = out.getvalue()

        self.assertIn("ReconcileOS Continuous Integrity Monitor", output)
        self.assertIn('"system_status": "DRIFT_DETECTED"', output)
        self.assertIn('"approvals_processed_count": 0', output)
        self.assertIn('"repairs_executed_count": 0', output)

        self.vpn_access.refresh_from_db()
        self.assertEqual(self.vpn_access.status, VPNAccessStatus.ENABLED)

    def test_full_fleet_continuous_monitoring_cycle(self):
        """
        Verify that fleet monitoring evaluates all employees across the directory,
        generates pending repair plans for all drift violations, and does not silently approve them.
        """
        emp2 = Employee.objects.create(
            full_name='Priya Sharma',
            email='priya.sharma@company.com',
            department='Sales',
            status=EmployeeStatus.TERMINATED
        )
        VPNAccess.objects.create(
            employee=emp2,
            status=VPNAccessStatus.ENABLED
        )

        self.vpn_access.enable()

        summary = self.monitor.run_monitoring_cycle()

        self.assertIsInstance(summary, dict)
        self.assertEqual(summary['employees_evaluated_count'], 2)
        self.assertEqual(summary['violations_detected_count'], 2)
        self.assertEqual(summary['repair_plans_generated_count'], 2)
        self.assertEqual(summary['approvals_processed_count'], 0)
        self.assertEqual(summary['repairs_executed_count'], 0)
        self.assertEqual(summary['remaining_open_violations_count'], 2)
        self.assertEqual(summary['system_status'], 'DRIFT_DETECTED')

        # Both employees must still have ENABLED VPN until human approval
        self.vpn_access.refresh_from_db()
        self.assertEqual(self.vpn_access.status, VPNAccessStatus.ENABLED)
