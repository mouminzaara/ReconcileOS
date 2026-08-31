"""
Automated unit tests for GitHub Connector Integration (Milestone 14).
"""

import urllib.error
from unittest.mock import patch, MagicMock
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.employees.models import Employee, EmployeeStatus
from apps.connectors.models import GitHubMembership, GitHubAccessStatus
from apps.connectors.adapters import ConnectorRegistry, GitHubConnectorAdapter, ConnectorException
from apps.rules.models import Rule, RuleSeverity
from apps.reconciliation.models import IntegrityViolation, ViolationStatus
from apps.reconciliation.engine import ReconciliationEngine
from apps.reconciliation.collectors import StateCollector
from apps.workflows.planner import RepairPlanner
from apps.workflows.executor import RepairExecutor
from apps.workflows.models import RepairPlan, PlanStatus, RepairVerification, VerificationResult
from apps.approvals.models import ApprovalRequest
from apps.approvals.services import ApprovalService


class GitHubConnectorTestCase(TestCase):
    """
    Test suite for GitHub Connector Integration (Milestone 14):
    - Membership query (MEMBER vs REVOKED)
    - Access revocation (DELETE /orgs/{org}/members/{user})
    - Pre-check idempotency handling
    - Authentication failure handling
    - Full self-healing reconciliation flow for INV-RULE-002
    """

    def setUp(self):
        self.client = APIClient()
        self.github_adapter = GitHubConnectorAdapter()

        # 1. Create Invariant Rule for GitHub Access
        self.rule = Rule.objects.create(
            rule_code='INV-RULE-002',
            name='Terminated Employee GitHub Access Revocation',
            description='Terminated employees must not retain GitHub organization membership.',
            source_system='HR',
            condition_attribute='status',
            condition_value='TERMINATED',
            target_system='GitHub',
            expected_attribute='status',
            expected_value='REVOKED',
            severity=RuleSeverity.HIGH,
            is_enabled=True
        )

        # 2. Create Employee Rahul Kumar (TERMINATED)
        self.employee = Employee.objects.create(
            full_name='Rahul Kumar',
            email='rahul.kumar@company.com',
            department='Engineering',
            status=EmployeeStatus.TERMINATED
        )

        # 3. Create GitHub Membership (MEMBER) -> Authorization Drift
        self.github_membership = GitHubMembership.objects.create(
            employee=self.employee,
            github_username='rahulkumar_gh',
            org_name='reconcileos-org',
            status=GitHubAccessStatus.MEMBER
        )

    def test_get_membership_status_mock_mode(self):
        """
        Verify membership query in mock mode returns MEMBER when database status is MEMBER.
        """
        info = self.github_adapter.get_membership_status(self.employee)

        self.assertTrue(info['connected'])
        self.assertEqual(info['access_status'], GitHubAccessStatus.MEMBER)
        self.assertEqual(info['username'], 'rahulkumar_gh')
        self.assertEqual(info['org_name'], 'reconcileos-org')

    @patch('urllib.request.urlopen')
    def test_get_membership_status_live_api_member(self, mock_urlopen):
        """
        Verify GET /orgs/{org}/members/{user} returning 204 indicates MEMBER status.
        """
        self.github_adapter.token = 'mock-github-token-123'

        mock_resp = MagicMock()
        mock_resp.status = 204
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        info = self.github_adapter.get_membership_status(self.employee)

        self.assertEqual(info['access_status'], GitHubAccessStatus.MEMBER)
        self.assertEqual(info['username'], 'rahulkumar_gh')

    @patch('urllib.request.urlopen')
    def test_get_membership_status_live_api_revoked(self, mock_urlopen):
        """
        Verify GET /orgs/{org}/members/{user} returning 404 indicates REVOKED status.
        """
        self.github_adapter.token = 'mock-github-token-123'
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url='', code=404, msg='Not Found', hdrs={}, fp=None
        )

        info = self.github_adapter.get_membership_status(self.employee)

        self.assertEqual(info['access_status'], GitHubAccessStatus.REVOKED)

    @patch('urllib.request.urlopen')
    def test_execute_action_live_api_revoke_success(self, mock_urlopen):
        """
        Verify DELETE /orgs/{org}/members/{user} returning 204 successfully revokes access.
        """
        self.github_adapter.token = 'mock-github-token-123'

        # 1st call for pre-check (returns MEMBER)
        mock_resp1 = MagicMock()
        mock_resp1.status = 204
        mock_resp1.__enter__.return_value = mock_resp1

        # 2nd call for DELETE (returns 204)
        mock_resp2 = MagicMock()
        mock_resp2.status = 204
        mock_resp2.__enter__.return_value = mock_resp2

        mock_urlopen.side_effect = [mock_resp1, mock_resp2]

        result = self.github_adapter.execute_action(self.employee, "SET GITHUB ACCESS TO REVOKED")

        self.assertTrue(result['success'])
        self.assertTrue(result['details']['status_changed'])
        self.assertEqual(result['details']['access_status'], GitHubAccessStatus.REVOKED)

        self.github_membership.refresh_from_db()
        self.assertEqual(self.github_membership.status, GitHubAccessStatus.REVOKED)

    @patch('urllib.request.urlopen')
    def test_execute_action_auth_failure_handling(self, mock_urlopen):
        """
        Verify HTTP 401/403 authorization failure raises clean ConnectorException.
        """
        self.github_adapter.token = 'invalid-token'
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url='', code=401, msg='Unauthorized', hdrs={}, fp=None
        )

        with self.assertRaises(ConnectorException) as ctx:
            self.github_adapter.execute_action(self.employee, "REMOVE GITHUB ACCESS")

        self.assertIn("Authentication / Authorization failure", str(ctx.exception))

    def test_full_reconciliation_and_self_healing_flow_for_github_rule(self):
        """
        Verify full end-to-end self-healing flow for GitHub invariant rule (INV-RULE-002):
        1. ReconciliationEngine detects violation (HR TERMINATED, GitHub MEMBER).
        2. RepairPlanner generates plan (SET GITHUB ACCESS TO REVOKED).
        3. Approval granted.
        4. RepairExecutor calls GitHubConnectorAdapter to revoke access.
        5. PostRepairVerifier confirms GitHub access is REVOKED.
        6. Violation resolved, plan completed.
        """
        # Step 1: Detect violation
        engine = ReconciliationEngine()
        engine.evaluate_employee_rules(str(self.employee.id))
        violation = IntegrityViolation.objects.get(
            employee=self.employee,
            affected_system='GitHub',
            status=ViolationStatus.OPEN
        )

        # Step 2: Generate repair plan
        planner = RepairPlanner()
        plan, _ = planner.plan_for_violation(violation)
        self.assertEqual(plan.target_system, 'GitHub')

        # Step 3: Approve repair plan
        approval_req = ApprovalRequest.objects.get(repair_plan=plan)
        ApprovalService.approve_request(approval_req, comment="Approved GitHub revocation")
        plan.refresh_from_db()

        # Step 4: Execute repair plan
        executor = RepairExecutor()
        log = executor.execute_plan(plan)

        self.plan = plan
        self.plan.refresh_from_db()
        violation.refresh_from_db()
        self.github_membership.refresh_from_db()

        # Step 5: Verification assertions
        self.assertEqual(self.github_membership.status, GitHubAccessStatus.REVOKED)
        self.assertEqual(self.plan.status, PlanStatus.COMPLETED)
        self.assertEqual(violation.status, ViolationStatus.RESOLVED)

        verification = RepairVerification.objects.get(repair_plan=self.plan)
        self.assertEqual(verification.result, VerificationResult.VERIFIED)
        self.assertEqual(verification.actual_state, 'REVOKED')
