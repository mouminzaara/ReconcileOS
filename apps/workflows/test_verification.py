"""
Automated unit tests for ReconcileOS Post-Repair Verification Engine (Milestone 10).
"""

from django.test import TestCase
from django.core.management import call_command
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from io import StringIO
from unittest.mock import patch

from apps.employees.models import Employee, EmployeeStatus
from apps.connectors.models import VPNAccess, VPNAccessStatus
from apps.rules.models import Rule, RuleSeverity
from apps.accounts.models import UserProfile, UserRole
from apps.reconciliation.models import IntegrityViolation, ViolationStatus
from apps.reconciliation.engine import ReconciliationEngine
from apps.reconciliation.collectors import StateCollector
from apps.workflows.models import RepairPlan, PlanStatus, RepairVerification, VerificationResult
from apps.workflows.planner import RepairPlanner
from apps.workflows.executor import RepairExecutor
from apps.workflows.verifier import PostRepairVerifier
from apps.approvals.models import ApprovalRequest, ApprovalDecision
from apps.approvals.services import ApprovalService


class PostRepairVerificationTestCase(TestCase):
    """
    Test suite for Post-Repair Verification Engine.
    """

    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser('admin_verif', 'admin@verif.com', 'admin123')
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

        ApprovalService.approve_request(self.approval_request)
        self.plan.refresh_from_db()

        self.executor = RepairExecutor()
        self.verifier = PostRepairVerifier()

    def test_successful_repair_followed_by_successful_verification(self):
        """
        Test 1: Successful repair execution followed by successful empirical verification.
        """
        log = self.executor.execute_plan(self.plan)

        self.plan.refresh_from_db()
        self.violation.refresh_from_db()
        self.vpn_access.refresh_from_db()

        verification = RepairVerification.objects.get(repair_plan=self.plan)

        self.assertEqual(verification.result, VerificationResult.VERIFIED)
        self.assertEqual(verification.expected_state, 'DISABLED')
        self.assertEqual(verification.actual_state, 'DISABLED')
        self.assertIsNotNone(verification.verified_at)

        self.assertEqual(self.plan.status, PlanStatus.COMPLETED)
        self.assertEqual(self.violation.status, ViolationStatus.RESOLVED)
        self.assertEqual(self.vpn_access.status, VPNAccessStatus.DISABLED)

    def test_repair_succeeds_but_verification_detects_incorrect_state(self):
        """
        Test 2: Repair executor action succeeds, but verification re-queries the system
        and detects non-compliant state.
        """
        mock_collected_state = {
            "employee_id": str(self.employee.id),
            "employee_status": "TERMINATED",
            "systems": {
                "vpn": {
                    "connected": True,
                    "access_status": "ENABLED"
                }
            }
        }

        with patch.object(StateCollector, 'collect_employee_state', return_value=mock_collected_state):
            verification = self.verifier.verify_repair(self.plan)

        self.plan.refresh_from_db()
        self.violation.refresh_from_db()

        self.assertEqual(verification.result, VerificationResult.VERIFICATION_FAILED)
        self.assertEqual(verification.expected_state, 'DISABLED')
        self.assertEqual(verification.actual_state, 'ENABLED')
        self.assertIn("Post-repair verification FAILED", verification.details)

        self.assertEqual(self.plan.status, PlanStatus.FAILED)
        self.assertEqual(self.violation.status, ViolationStatus.OPEN)

    def test_verify_repair_management_command(self):
        """
        Test execution of verify_repair management command.
        """
        self.executor.execute_plan(self.plan)

        out = StringIO()
        call_command('verify_repair', '--plan-id', str(self.plan.id), stdout=out)
        output = out.getvalue()

        self.assertIn("[VERIFICATION SUCCESS]", output)
        self.assertIn("COMPLETED", output)
        self.assertIn("RESOLVED", output)

    def test_verify_repair_api_endpoint(self):
        """
        Test REST API endpoint POST /api/v1/workflows/plans/<id>/verify/.
        """
        self.executor.execute_plan(self.plan)

        verify_url = f"/api/v1/workflows/plans/{self.plan.id}/verify/"
        response = self.client.post(verify_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['verification_result'], 'VERIFIED')
        self.assertEqual(response.data['plan_status'], 'COMPLETED')


class FullLifecycleTerminationE2ETestCase(TestCase):
    """
    Focused end-to-end regression test for the complete employee-termination
    reconciliation lifecycle in an isolated test environment.
    """

    def setUp(self):
        self.admin_user = User.objects.create_superuser('admin_e2e', 'admin@e2e.com', 'admin123')
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

        # 1. Start with an ACTIVE employee and active VPN access
        self.employee = Employee.objects.create(
            full_name='Maya Lin',
            email='maya.lin@company.com',
            department='Engineering',
            status=EmployeeStatus.ACTIVE
        )

        self.vpn_access = VPNAccess.objects.create(
            employee=self.employee,
            status=VPNAccessStatus.ENABLED
        )

    def test_complete_employee_termination_reconciliation_lifecycle(self):
        """
        Verify the end-to-end reconciliation lifecycle:
        Active employee -> termination -> drift detection -> violation creation ->
        repair-plan generation -> pending approval -> human approval ->
        simulated repair execution -> independent post-repair verification ->
        violation resolution -> audit-chain verification.
        """
        from apps.audit.services import AuditLogger
        from apps.audit.models import AuditEventType, AuditLog
        from apps.workflows.executor import IneligiblePlanExecutionException

        correlation_id = "e2e-term-test-corr-001"

        # Step 1: Initial state evaluation while employee is ACTIVE
        engine = ReconciliationEngine()
        initial_report = engine.evaluate_employee_rules(self.employee, correlation_id=correlation_id)
        self.assertEqual(initial_report['violations_detected_count'], 0)
        self.assertEqual(IntegrityViolation.objects.filter(employee=self.employee).count(), 0)

        # Step 2: Terminate the employee in HR system
        status_changed = self.employee.terminate()
        self.assertTrue(status_changed)
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.status, EmployeeStatus.TERMINATED)

        # Step 3: Drift Detection & Violation Creation
        reconcile_report = engine.evaluate_employee_rules(self.employee, correlation_id=correlation_id)
        self.assertEqual(reconcile_report['violations_detected_count'], 1)

        violation = IntegrityViolation.objects.get(employee=self.employee, rule=self.rule)
        self.assertEqual(violation.status, ViolationStatus.OPEN)
        self.assertEqual(violation.affected_system, 'VPN')
        self.assertEqual(violation.expected_state, 'DISABLED')
        self.assertEqual(violation.actual_state, 'ENABLED')
        self.assertEqual(violation.severity, RuleSeverity.CRITICAL)

        # Step 4: Repair Plan Generation (Idempotent and deterministic)
        planner = RepairPlanner()
        plan, created = planner.plan_for_violation(violation, correlation_id=correlation_id)
        self.assertTrue(created)
        self.assertEqual(plan.status, PlanStatus.PENDING)
        self.assertEqual(plan.action, 'DISABLE VPN ACCESS')
        self.assertEqual(plan.target_system, 'VPN')

        # Step 5: Verify Pending Approval Request exists
        approval_request = ApprovalRequest.objects.get(repair_plan=plan)
        self.assertEqual(approval_request.decision, ApprovalDecision.PENDING)

        # Step 6: Verify unapproved repair cannot execute
        executor = RepairExecutor()
        with self.assertRaises(IneligiblePlanExecutionException):
            executor.execute_plan(plan, executed_by=self.admin_user, correlation_id=correlation_id)

        # Downstream VPN state must remain unchanged at this point
        self.vpn_access.refresh_from_db()
        self.assertEqual(self.vpn_access.status, VPNAccessStatus.ENABLED)

        # Step 7: Human Approval Decision
        ApprovalService.approve_request(
            approval_request,
            decided_by=self.admin_user,
            comment="Approved for employee offboarding remediation",
            correlation_id=correlation_id
        )
        plan.refresh_from_db()
        self.assertEqual(plan.status, PlanStatus.APPROVED)

        # Step 8: Repair Execution & Downstream State Mutation
        exec_log = executor.execute_plan(plan, executed_by=self.admin_user, correlation_id=correlation_id)
        self.assertEqual(exec_log.status, "SUCCESS")

        # Downstream VPN state must now be DISABLED
        self.vpn_access.refresh_from_db()
        self.assertEqual(self.vpn_access.status, VPNAccessStatus.DISABLED)

        # Step 9: Post-Repair Verification & Violation Resolution
        plan.refresh_from_db()
        violation.refresh_from_db()

        self.assertEqual(plan.status, PlanStatus.COMPLETED)
        self.assertEqual(violation.status, ViolationStatus.RESOLVED)

        verification = RepairVerification.objects.get(repair_plan=plan)
        self.assertEqual(verification.result, VerificationResult.VERIFIED)
        self.assertEqual(verification.expected_state, 'DISABLED')
        self.assertEqual(verification.actual_state, 'DISABLED')

        # Step 10: Cryptographic Audit Hash Chain Integrity Verification
        audit_events = list(AuditLog.objects.filter(correlation_id=correlation_id).order_by('timestamp', 'id'))
        event_types = [e.event_type for e in audit_events]

        self.assertIn(AuditEventType.RULE_EVALUATED, event_types)
        self.assertIn(AuditEventType.VIOLATION_DETECTED, event_types)
        self.assertIn(AuditEventType.REPAIR_PLAN_CREATED, event_types)
        self.assertIn(AuditEventType.APPROVAL_REQUESTED, event_types)
        self.assertIn(AuditEventType.REPAIR_APPROVED, event_types)
        self.assertIn(AuditEventType.REPAIR_EXECUTED, event_types)
        self.assertIn(AuditEventType.VERIFICATION_PERFORMED, event_types)
        self.assertIn(AuditEventType.VIOLATION_RESOLVED, event_types)

        is_valid, msg, details = AuditLogger.verify_chain_integrity()
        self.assertTrue(is_valid, f"Audit chain verification failed: {msg}")
        self.assertGreaterEqual(details['verified_records'], len(audit_events))

