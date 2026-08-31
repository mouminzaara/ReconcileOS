"""
Automated unit tests for ReconcileOS Idempotent Repair Operations (Milestone 12).
"""

from django.test import TestCase
from django.core.management import call_command
from rest_framework.test import APIClient
from rest_framework import status
from io import StringIO

from apps.employees.models import Employee, EmployeeStatus
from apps.connectors.models import VPNAccess, VPNAccessStatus
from apps.connectors.adapters import ConnectorRegistry, VPNConnectorAdapter
from apps.rules.models import Rule, RuleSeverity
from apps.reconciliation.models import IntegrityViolation, ViolationStatus
from apps.reconciliation.engine import ReconciliationEngine
from apps.workflows.models import RepairPlan, PlanStatus, RepairExecutionLog, ExecutionStatus, RepairVerification, VerificationResult
from apps.workflows.planner import RepairPlanner
from apps.workflows.executor import RepairExecutor, IneligiblePlanExecutionException
from apps.approvals.models import ApprovalRequest
from apps.approvals.services import ApprovalService


class IdempotentRepairOperationsTestCase(TestCase):
    """
    Test suite for Idempotent Repair Operations (Milestone 12):
    1. First disable succeeds.
    2. Same operation requested again.
    3. System recognizes desired state already exists (DISABLED).
    4. No unnecessary duplicate action is performed.
    5. Timeout followed by state check.
    6. State already correct after timeout.
    """

    def setUp(self):
        self.client = APIClient()
        self.vpn_connector = ConnectorRegistry.get_connector('vpn')

        # 1. Create Invariant Rule
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

        # 2. Create Employee Rahul Kumar (TERMINATED)
        self.employee = Employee.objects.create(
            full_name='Rahul Kumar',
            email='rahul.kumar@company.com',
            department='Engineering',
            status=EmployeeStatus.TERMINATED
        )

        # 3. Create Downstream VPN Access (ENABLED) -> Authorization Drift
        self.vpn_access = VPNAccess.objects.create(
            employee=self.employee,
            status=VPNAccessStatus.ENABLED
        )

        # 4. Detect violation & create repair plan
        self.engine = ReconciliationEngine()
        self.engine.evaluate_employee_rules(str(self.employee.id))
        self.violation = IntegrityViolation.objects.get(employee=self.employee, status=ViolationStatus.OPEN)

        self.planner = RepairPlanner()
        self.plan, _ = self.planner.plan_for_violation(self.violation)
        self.approval_request = ApprovalRequest.objects.get(repair_plan=self.plan)

        # Approve repair plan
        ApprovalService.approve_request(self.approval_request)
        self.plan.refresh_from_db()

        self.executor = RepairExecutor()

    def test_first_disable_succeeds_and_records_idempotency_key(self):
        """
        Test 1 & 4: First disable attempt succeeds and records idempotency key and attempt details.
        """
        log = self.executor.execute_plan(self.plan)

        self.plan.refresh_from_db()
        self.vpn_access.refresh_from_db()

        self.assertEqual(log.status, ExecutionStatus.SUCCESS)
        self.assertEqual(log.attempt_number, 1)
        self.assertTrue(log.idempotency_key.startswith("idemp_"))
        self.assertEqual(self.vpn_access.status, VPNAccessStatus.DISABLED)
        self.assertEqual(self.plan.status, PlanStatus.COMPLETED)

    def test_pre_execution_check_recognizes_desired_state_already_exists(self):
        """
        Test 2, 3, & 4: If target VPN state is ALREADY DISABLED when execution is triggered,
        the system recognizes the desired state already exists, treats the repair as satisfied,
        and performs NO unnecessary duplicate downstream mutation.
        """
        # Explicitly set VPN state to DISABLED before execution
        self.vpn_access.disable()
        self.vpn_access.refresh_from_db()
        self.assertEqual(self.vpn_access.status, VPNAccessStatus.DISABLED)

        # Trigger execution on plan
        log = self.executor.execute_plan(self.plan)

        self.plan.refresh_from_db()
        self.violation.refresh_from_db()

        # Log assertions
        self.assertEqual(log.status, ExecutionStatus.SUCCESS)
        self.assertTrue(log.already_satisfied)
        self.assertIn("already 'DISABLED'", log.output_message)

        # Plan & Violation status
        self.assertEqual(self.plan.status, PlanStatus.COMPLETED)
        self.assertEqual(self.violation.status, ViolationStatus.RESOLVED)

    def test_timeout_followed_by_state_check_where_state_already_correct(self):
        """
        Test 5 & 6: Timeout followed by state check.
        Attempt 1: Simulates API gateway timeout AFTER downstream state was updated to DISABLED.
        Attempt 2 (Retry): Pre-execution state check queries target system, sees state is ALREADY DISABLED,
        and completes idempotently without re-sending disable action.
        """
        # Configure simulated failure where downstream state was applied before timeout
        self.vpn_connector.set_simulated_failure(fail_next_n=1, apply_state_first=True)

        # Execute plan with retry enabled
        log = self.executor.execute_plan(self.plan, max_retries=3, auto_retry=True)

        self.plan.refresh_from_db()
        self.violation.refresh_from_db()
        self.vpn_access.refresh_from_db()

        logs = list(RepairExecutionLog.objects.filter(repair_plan=self.plan).order_by('attempt_number'))
        self.assertEqual(len(logs), 2)

        # Attempt #1 (Timeout after mutation)
        attempt1 = logs[0]
        self.assertEqual(attempt1.attempt_number, 1)
        self.assertEqual(attempt1.status, ExecutionStatus.FAILED)
        self.assertIn("gateway timeout AFTER state update", attempt1.error_details)

        # Attempt #2 (Pre-check recognizes desired state already satisfied)
        attempt2 = logs[1]
        self.assertEqual(attempt2.attempt_number, 2)
        self.assertEqual(attempt2.status, ExecutionStatus.SUCCESS)
        self.assertTrue(attempt2.already_satisfied)
        self.assertIn("already 'DISABLED'", attempt2.output_message)

        # Post-repair verification & final state assertions
        verification = RepairVerification.objects.get(repair_plan=self.plan)
        self.assertEqual(verification.result, VerificationResult.VERIFIED)
        self.assertEqual(self.vpn_access.status, VPNAccessStatus.DISABLED)
        self.assertEqual(self.plan.status, PlanStatus.COMPLETED)
        self.assertEqual(self.violation.status, ViolationStatus.RESOLVED)

    def test_idempotent_re_execution_prevention_on_completed_plans(self):
        """
        Verify that attempting to re-execute an already COMPLETED plan is blocked cleanly by eligibility rules.
        """
        # Complete plan once
        self.executor.execute_plan(self.plan)
        self.plan.refresh_from_db()
        self.assertEqual(self.plan.status, PlanStatus.COMPLETED)

        # Re-executing must raise IneligiblePlanExecutionException
        with self.assertRaises(IneligiblePlanExecutionException) as ctx:
            self.executor.execute_plan(self.plan)

        self.assertIn("Redundant execution of successful operations is prevented", str(ctx.exception))
