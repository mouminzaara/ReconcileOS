"""
Comprehensive Concurrency and State Integrity Tests for Repair Execution Engine (Phase 2B).

Tests genuine concurrent execution using multi-threading (ThreadPoolExecutor / Barrier),
verifying that race conditions are safely resolved and duplicate downstream mutations are prevented.
"""

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.test import TransactionTestCase
from django.contrib.auth.models import User
from unittest.mock import patch

from apps.employees.models import Employee, EmployeeStatus
from apps.connectors.models import VPNAccess, VPNAccessStatus
from apps.connectors.adapters import ConnectorRegistry
from apps.rules.models import Rule, RuleSeverity
from apps.accounts.models import UserProfile, UserRole
from apps.reconciliation.models import IntegrityViolation, ViolationStatus
from apps.reconciliation.engine import ReconciliationEngine
from apps.workflows.models import RepairPlan, PlanStatus, RepairExecutionLog, ExecutionStatus
from apps.workflows.planner import RepairPlanner
from apps.workflows.executor import RepairExecutor, IneligiblePlanExecutionException, _execute_with_db_lock_retry
from apps.approvals.models import ApprovalRequest, ApprovalDecision
from apps.approvals.services import ApprovalService


class RepairExecutionConcurrencyTestCase(TransactionTestCase):
    """
    Genuine concurrent execution test suite using multi-threading.
    """

    def setUp(self):
        self.admin_user = User.objects.create_superuser('admin_race', 'admin_race@test.com', 'admin123')
        UserProfile.objects.create(user=self.admin_user, role=UserRole.ADMIN)

        self.rule = Rule.objects.create(
            rule_code='INV-CONCUR-001',
            name='Terminated Employee VPN Invariant',
            description='Terminated employees must have VPN disabled.',
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
            full_name='Concurrency Test Subject',
            email='concur@example.com',
            department='Engineering',
            status=EmployeeStatus.TERMINATED
        )

        self.vpn_access = VPNAccess.objects.create(
            employee=self.employee,
            status=VPNAccessStatus.ENABLED
        )

        # Trigger reconciliation to generate violation and plan
        engine = ReconciliationEngine()
        engine.evaluate_employee_rules(str(self.employee.id))
        self.violation = IntegrityViolation.objects.get(employee=self.employee, status=ViolationStatus.OPEN)

        planner = RepairPlanner()
        self.plan, _ = planner.plan_for_violation(self.violation)
        self.approval_request = ApprovalRequest.objects.get(repair_plan=self.plan)

        # Approve the plan
        ApprovalService.approve_request(self.approval_request, decided_by=self.admin_user, comment="Approved for concurrency test")
        self.plan.refresh_from_db()

    def test_concurrent_execution_of_same_approved_plan(self):
        """
        Verify that two genuine concurrent threads attempting to execute the same approved
        repair plan simultaneously result in:
        1. Exactly ONE successful execution.
        2. The other request being rejected with IneligiblePlanExecutionException.
        3. The downstream connector action executed exactly once.
        4. No duplicate execution logs or state corruption.
        """
        barrier = threading.Barrier(2)
        results = []
        errors = []

        def worker_task(worker_id):
            executor = RepairExecutor()
            try:
                # Synchronize threads so they hit execute_plan simultaneously
                barrier.wait(timeout=5)
                # Re-fetch instance to simulate independent web request handling
                plan = _execute_with_db_lock_retry(lambda: RepairPlan.objects.get(id=self.plan.id))
                log = executor.execute_plan(plan, executed_by=self.admin_user)
                results.append((worker_id, log))
            except IneligiblePlanExecutionException as exc:
                errors.append((worker_id, exc))
            except Exception as exc:
                errors.append((worker_id, exc))

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(worker_task, i) for i in range(2)]
            for f in as_completed(futures):
                f.result()

        # Exactly ONE thread must succeed
        self.assertEqual(len(results), 1, f"Expected exactly 1 successful execution, got {len(results)}. Errors: {errors}")
        # Exactly ONE thread must be rejected with IneligiblePlanExecutionException
        self.assertEqual(len(errors), 1, f"Expected exactly 1 ineligible exception, got {len(errors)}. Results: {results}")

        worker_id, exc = errors[0]
        self.assertIsInstance(exc, IneligiblePlanExecutionException)
        self.assertTrue(
            "currently executing" in str(exc) or "already" in str(exc),
            f"Unexpected exception message: {exc}"
        )

        # Final state checks
        self.plan.refresh_from_db()
        self.vpn_access.refresh_from_db()

        self.assertIn(self.plan.status, [PlanStatus.SUCCESS, PlanStatus.COMPLETED])
        self.assertEqual(self.vpn_access.status, VPNAccessStatus.DISABLED)

        # Downstream execution logs must reflect only the single execution
        logs = RepairExecutionLog.objects.filter(repair_plan=self.plan)
        self.assertEqual(logs.count(), 1)
        self.assertEqual(logs.first().status, ExecutionStatus.SUCCESS)

    def test_concurrent_request_after_one_completes(self):
        """
        Verify that a second execution request attempting to run after or while the plan
        is completed is safely rejected by idempotency safeguards.
        """
        executor = RepairExecutor()
        log1 = executor.execute_plan(self.plan, executed_by=self.admin_user)
        self.assertEqual(log1.status, ExecutionStatus.SUCCESS)

        self.plan.refresh_from_db()
        self.assertIn(self.plan.status, [PlanStatus.SUCCESS, PlanStatus.COMPLETED])

        # Second sequential or late-arriving concurrent request
        with self.assertRaises(IneligiblePlanExecutionException) as ctx:
            executor.execute_plan(self.plan, executed_by=self.admin_user)

        self.assertIn("Redundant execution of successful operations is prevented", str(ctx.exception))

    def test_pending_and_rejected_plans_remain_ineligible(self):
        """
        Preserve Phase 2A requirement:
        Verify that unapproved (PENDING) and REJECTED plans cannot be executed.
        """
        # Create unapproved plan
        plan2 = RepairPlan.objects.create(
            employee=self.employee,
            violation=self.violation,
            target_system='VPN',
            action='DISABLE VPN ACCESS',
            reason='Unapproved test plan',
            status=PlanStatus.PENDING
        )
        ApprovalRequest.objects.create(
            repair_plan=plan2,
            decision=ApprovalDecision.PENDING
        )

        executor = RepairExecutor()

        # 1. PENDING plan must be blocked
        with self.assertRaises(IneligiblePlanExecutionException) as ctx:
            executor.execute_plan(plan2, executed_by=self.admin_user)
        self.assertIn("Current status is 'PENDING'", str(ctx.exception))

        # 2. REJECTED plan must be blocked
        plan2.status = PlanStatus.REJECTED
        plan2.save()
        app_req = ApprovalRequest.objects.get(repair_plan=plan2)
        app_req.decision = ApprovalDecision.REJECTED
        app_req.save()

        with self.assertRaises(IneligiblePlanExecutionException) as ctx:
            executor.execute_plan(plan2, executed_by=self.admin_user)
        self.assertIn("Current status is 'REJECTED'", str(ctx.exception))

    def test_retry_behavior_does_not_duplicate_downstream_mutations(self):
        """
        Verify that retrying a plan after timeout recognizes desired state already exists
        and completes idempotently without re-executing downstream mutation.
        """
        vpn_connector = ConnectorRegistry.get_connector('vpn')
        # Simulate gateway timeout AFTER downstream mutation applied
        vpn_connector.set_simulated_failure(fail_next_n=1, apply_state_first=True)

        executor = RepairExecutor()
        log = executor.execute_plan(self.plan, executed_by=self.admin_user, max_retries=3, auto_retry=True)

        self.plan.refresh_from_db()
        self.vpn_access.refresh_from_db()

        logs = list(RepairExecutionLog.objects.filter(repair_plan=self.plan).order_by('attempt_number'))
        self.assertEqual(len(logs), 2)

        # Attempt 1 failed with timeout
        self.assertEqual(logs[0].status, ExecutionStatus.FAILED)
        # Attempt 2 succeeded via pre-check idempotency (state was already DISABLED)
        self.assertEqual(logs[1].status, ExecutionStatus.SUCCESS)
        self.assertTrue(logs[1].already_satisfied)
        self.assertEqual(self.vpn_access.status, VPNAccessStatus.DISABLED)
        self.assertIn(self.plan.status, [PlanStatus.SUCCESS, PlanStatus.COMPLETED])
