"""
Automated unit tests for ReconcileOS Fault-Tolerant Execution & Retry Engine (Milestone 11).
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


class FaultTolerantExecutionTestCase(TestCase):
    """
    Test suite for Fault-Tolerant Execution, Retry & Recovery Engine (Milestone 11).
    """

    def setUp(self):
        self.client = APIClient()

        # Retrieve or register VPNConnectorAdapter
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

    def test_full_retry_recovery_and_verification_flow(self):
        """
        Complete Milestone 11 Test Scenario:
        1. Rahul is TERMINATED.
        2. VPN is ENABLED.
        3. Drift is detected.
        4. Repair plan is approved.
        5. First disable attempt fails (simulated API failure).
        6. Failure is recorded (Attempt #1 log).
        7. Retry occurs.
        8. Retry succeeds (Attempt #2 log).
        9. VPN state is read again.
        10. Verification succeeds.
        """
        # Configure simulated failure on first attempt
        self.vpn_connector.set_simulated_failure(fail_next_n=1)

        # Execute repair with bounded retry
        final_log = self.executor.execute_plan(self.plan, max_retries=3, auto_retry=True)

        self.plan.refresh_from_db()
        self.violation.refresh_from_db()
        self.vpn_access.refresh_from_db()

        # Check execution log count (must be 2 attempts)
        logs = RepairExecutionLog.objects.filter(repair_plan=self.plan).order_by('attempt_number')
        self.assertEqual(logs.count(), 2)

        # Attempt #1 Log assertions
        attempt1 = logs[0]
        self.assertEqual(attempt1.attempt_number, 1)
        self.assertEqual(attempt1.status, ExecutionStatus.FAILED)
        self.assertIn("Simulated external VPN API failure", attempt1.error_details)
        self.assertIsNotNone(attempt1.operation_id)
        self.assertIsNotNone(attempt1.completed_at)

        # Attempt #2 Log assertions
        attempt2 = logs[1]
        self.assertEqual(attempt2.attempt_number, 2)
        self.assertEqual(attempt2.status, ExecutionStatus.SUCCESS)
        self.assertIn("Successfully disabled VPN access", attempt2.output_message)

        # Post-repair verification assertions
        verification = RepairVerification.objects.get(repair_plan=self.plan)
        self.assertEqual(verification.result, VerificationResult.VERIFIED)
        self.assertEqual(verification.actual_state, 'DISABLED')

        # Final statuses
        self.assertEqual(self.plan.status, PlanStatus.COMPLETED)
        self.assertEqual(self.violation.status, ViolationStatus.RESOLVED)
        self.assertEqual(self.vpn_access.status, VPNAccessStatus.DISABLED)

    def test_idempotency_prevents_unnecessary_execution_repeats(self):
        """
        Verify that an already completed/successful repair operation is NOT repeated unnecessarily.
        """
        # Execute plan once to completion
        self.executor.execute_plan(self.plan)
        self.plan.refresh_from_db()
        self.assertEqual(self.plan.status, PlanStatus.COMPLETED)

        # Count logs after first run
        initial_log_count = RepairExecutionLog.objects.filter(repair_plan=self.plan).count()

        # Attempt to execute completed plan again -> must raise IneligiblePlanExecutionException
        with self.assertRaises(IneligiblePlanExecutionException) as ctx:
            self.executor.execute_plan(self.plan)

        self.assertIn("Operation is already 'COMPLETED'", str(ctx.exception))
        self.assertIn("Redundant execution of successful operations is prevented", str(ctx.exception))

        # Confirm log count did NOT increase
        new_log_count = RepairExecutionLog.objects.filter(repair_plan=self.plan).count()
        self.assertEqual(initial_log_count, new_log_count)
