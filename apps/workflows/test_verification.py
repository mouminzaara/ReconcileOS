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
from apps.approvals.models import ApprovalRequest
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
