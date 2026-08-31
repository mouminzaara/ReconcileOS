"""
Automated unit tests for Additional Simulated Connected Systems (Milestone 15).
"""

from django.test import TestCase
from rest_framework.test import APIClient

from apps.employees.models import Employee, EmployeeStatus
from apps.connectors.models import (
    VPNAccess, VPNAccessStatus,
    GitHubMembership, GitHubAccessStatus,
    CloudIAMAccess, CloudRole,
    SlackAccount, SlackAccountStatus
)
from apps.connectors.adapters import ConnectorRegistry, CloudConnectorAdapter, SlackConnectorAdapter
from apps.rules.models import Rule, RuleSeverity
from apps.reconciliation.models import IntegrityViolation, ViolationStatus
from apps.reconciliation.engine import ReconciliationEngine
from apps.reconciliation.collectors import StateCollector
from apps.reconciliation.monitor import ContinuousMonitor
from apps.workflows.models import RepairPlan, PlanStatus, RepairVerification, VerificationResult


class AdditionalConnectorsTestCase(TestCase):
    """
    Test suite for Cloud IAM & Slack Connector Adapters (Milestone 15):
    - Cloud role inspection & revocation
    - Slack account status inspection & deactivation
    - Pre-check idempotency handling
    - Full 5-system multi-drift self-healing cycle
    """

    def setUp(self):
        self.client = APIClient()
        self.cloud_adapter = CloudConnectorAdapter()
        self.slack_adapter = SlackConnectorAdapter()

        # Seed Rules
        self.rule_vpn = Rule.objects.create(
            rule_code='INV-RULE-001', name='VPN Rule', source_system='HR',
            condition_attribute='status', condition_value='TERMINATED',
            target_system='VPN', expected_attribute='status', expected_value='DISABLED',
            severity=RuleSeverity.CRITICAL, is_enabled=True
        )
        self.rule_github = Rule.objects.create(
            rule_code='INV-RULE-002', name='GitHub Rule', source_system='HR',
            condition_attribute='status', condition_value='TERMINATED',
            target_system='GitHub', expected_attribute='status', expected_value='REVOKED',
            severity=RuleSeverity.HIGH, is_enabled=True
        )
        self.rule_cloud = Rule.objects.create(
            rule_code='INV-RULE-003', name='Cloud IAM Rule', source_system='HR',
            condition_attribute='status', condition_value='TERMINATED',
            target_system='Cloud', expected_attribute='access_status', expected_value='NO_ROLE',
            severity=RuleSeverity.CRITICAL, is_enabled=True
        )
        self.rule_slack = Rule.objects.create(
            rule_code='INV-RULE-004', name='Slack Rule', source_system='HR',
            condition_attribute='status', condition_value='TERMINATED',
            target_system='Slack', expected_attribute='access_status', expected_value='DEACTIVATED',
            severity=RuleSeverity.HIGH, is_enabled=True
        )

        # Seed Employee Rahul (TERMINATED)
        self.employee = Employee.objects.create(
            full_name='Rahul Kumar',
            email='rahul.kumar@company.com',
            department='Engineering',
            status=EmployeeStatus.TERMINATED
        )

        # Seed 4 connected system drift records
        self.vpn_access = VPNAccess.objects.create(employee=self.employee, status=VPNAccessStatus.ENABLED)
        self.github_membership = GitHubMembership.objects.create(
            employee=self.employee, github_username='rahulkumar_gh', status=GitHubAccessStatus.MEMBER
        )
        self.cloud_access = CloudIAMAccess.objects.create(
            employee=self.employee, cloud_identity='arn:aws:iam::123:user/rahul', role=CloudRole.DEVELOPER_ROLE
        )
        self.slack_account = SlackAccount.objects.create(
            employee=self.employee, slack_user_id='U10293847', status=SlackAccountStatus.ACTIVE
        )

    def test_cloud_connector_revocation_and_idempotency(self):
        """
        Verify CloudIAMAccess role revocation (DEVELOPER_ROLE -> NO_ROLE) and idempotency.
        """
        self.assertEqual(self.cloud_access.role, CloudRole.DEVELOPER_ROLE)

        # Action 1: Revoke
        res1 = self.cloud_adapter.execute_action(self.employee, "REVOKE CLOUD PERMISSIONS")
        self.assertTrue(res1['success'])
        self.assertTrue(res1['details']['status_changed'])

        self.cloud_access.refresh_from_db()
        self.assertEqual(self.cloud_access.role, CloudRole.NO_ROLE)

        # Action 2: Repeat (Idempotent pre-check)
        res2 = self.cloud_adapter.execute_action(self.employee, "REVOKE CLOUD PERMISSIONS")
        self.assertTrue(res2['success'])
        self.assertTrue(res2['details']['already_satisfied'])
        self.assertFalse(res2['details']['status_changed'])

    def test_slack_connector_deactivation_and_idempotency(self):
        """
        Verify SlackAccount deactivation (ACTIVE -> DEACTIVATED) and idempotency.
        """
        self.assertEqual(self.slack_account.status, SlackAccountStatus.ACTIVE)

        # Action 1: Deactivate
        res1 = self.slack_adapter.execute_action(self.employee, "DEACTIVATE SLACK ACCOUNT")
        self.assertTrue(res1['success'])
        self.assertTrue(res1['details']['status_changed'])

        self.slack_account.refresh_from_db()
        self.assertEqual(self.slack_account.status, SlackAccountStatus.DEACTIVATED)

        # Action 2: Repeat (Idempotent pre-check)
        res2 = self.slack_adapter.execute_action(self.employee, "DEACTIVATE SLACK ACCOUNT")
        self.assertTrue(res2['success'])
        self.assertTrue(res2['details']['already_satisfied'])
        self.assertFalse(res2['details']['status_changed'])

    def test_unified_state_collector_gathers_all_four_systems(self):
        """
        Verify StateCollector retrieves state for HR, VPN, GitHub, Cloud, and Slack.
        """
        collector = StateCollector()
        state = collector.collect_employee_state(self.employee)

        self.assertEqual(state['employee_status'], 'TERMINATED')
        systems = state['systems']
        self.assertEqual(systems['vpn']['access_status'], 'ENABLED')
        self.assertEqual(systems['github']['access_status'], 'MEMBER')
        self.assertEqual(systems['cloud']['access_status'], 'DEVELOPER_ROLE')
        self.assertEqual(systems['slack']['access_status'], 'ACTIVE')

    def test_full_five_system_reconciliation_and_self_healing_cycle(self):
        """
        Verify continuous monitoring cycle resolves all 4 downstream drift violations for Rahul:
        HR: TERMINATED
        VPN: ENABLED -> DISABLED
        GitHub: MEMBER -> REVOKED
        Cloud: DEVELOPER_ROLE -> NO_ROLE
        Slack: ACTIVE -> DEACTIVATED
        Result: CONSISTENT (0 open violations)
        """
        monitor = ContinuousMonitor()
        summary = monitor.run_monitoring_cycle(employee_id=str(self.employee.id), auto_approve_policy=True)

        self.assertEqual(summary['violations_detected_count'], 4)
        self.assertEqual(summary['repairs_executed_count'], 4)
        self.assertEqual(summary['verifications_completed_count'], 4)
        self.assertEqual(summary['system_status'], 'CONSISTENT')
        self.assertEqual(summary['remaining_open_violations_count'], 0)

        # Verify all downstream models updated to non-privileged compliant states
        self.vpn_access.refresh_from_db()
        self.github_membership.refresh_from_db()
        self.cloud_access.refresh_from_db()
        self.slack_account.refresh_from_db()

        self.assertEqual(self.vpn_access.status, VPNAccessStatus.DISABLED)
        self.assertEqual(self.github_membership.status, GitHubAccessStatus.REVOKED)
        self.assertEqual(self.cloud_access.role, CloudRole.NO_ROLE)
        self.assertEqual(self.slack_account.status, SlackAccountStatus.DEACTIVATED)
