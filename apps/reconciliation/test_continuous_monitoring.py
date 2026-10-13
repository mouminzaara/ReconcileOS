"""
Automated unit tests for ReconcileOS Continuous Integrity Monitoring Engine (Milestone 13).
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
from apps.reconciliation.monitor import ContinuousMonitor
from apps.workflows.models import RepairPlan, PlanStatus, RepairVerification, VerificationResult


class ContinuousIntegrityMonitoringTestCase(TestCase):
    """
    Test suite for Continuous Integrity Monitoring Engine (Milestone 13).
    """

    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser('admin_mon', 'admin@mon.com', 'admin123')
        UserProfile.objects.create(user=self.admin_user, role=UserRole.ADMIN)

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

    def test_simulated_admin_drift_and_continuous_self_healing_cycle(self):
        """
        Full Milestone 13 Demonstration Test:
        1. Initially: HR: TERMINATED, VPN: DISABLED -> CONSISTENT.
        2. Admin manually re-enables VPN -> VPN: ENABLED.
        3. ContinuousMonitor runs audit cycle.
        4. Detects drift (HR: TERMINATED, VPN: ENABLED).
        5. Generates repair plan, auto-approves policy, executes repair via VPNConnectorAdapter.
        6. Empirical verification succeeds (VPN: DISABLED).
        7. System returns to CONSISTENT.
        """
        summary1 = self.monitor.run_monitoring_cycle(employee_id=str(self.employee.id))
        self.assertEqual(summary1['system_status'], 'CONSISTENT')

        self.vpn_access.enable()
        self.vpn_access.refresh_from_db()
        self.assertEqual(self.vpn_access.status, VPNAccessStatus.ENABLED)

        summary2 = self.monitor.run_monitoring_cycle(
            employee_id=str(self.employee.id),
            auto_approve_policy=True
        )

        self.assertEqual(summary2['violations_detected_count'], 1)
        self.assertEqual(summary2['repair_plans_generated_count'], 1)
        self.assertEqual(summary2['approvals_processed_count'], 1)
        self.assertEqual(summary2['repairs_executed_count'], 1)
        self.assertEqual(summary2['verifications_completed_count'], 1)
        self.assertEqual(summary2['system_status'], 'CONSISTENT')

        self.vpn_access.refresh_from_db()
        self.assertEqual(self.vpn_access.status, VPNAccessStatus.DISABLED)

        violation = IntegrityViolation.objects.get(employee=self.employee, affected_system='VPN')
        self.assertEqual(violation.status, ViolationStatus.RESOLVED)

        plan = RepairPlan.objects.get(violation=violation)
        self.assertEqual(plan.status, PlanStatus.COMPLETED)

        verification = RepairVerification.objects.get(repair_plan=plan)
        self.assertEqual(verification.result, VerificationResult.VERIFIED)

    def test_run_continuous_monitor_management_command(self):
        """
        Test execution of run_continuous_monitor management command.
        """
        self.vpn_access.enable()

        out = StringIO()
        call_command(
            'run_continuous_monitor',
            '--once',
            '--employee-id', str(self.employee.id),
            '--auto-approve',
            stdout=out
        )
        output = out.getvalue()

        self.assertIn("ReconcileOS Continuous Integrity Monitor", output)
        self.assertIn('"system_status": "CONSISTENT"', output)

        self.vpn_access.refresh_from_db()
        self.assertEqual(self.vpn_access.status, VPNAccessStatus.DISABLED)

    def test_continuous_monitor_api_endpoint(self):
        """
        Test REST API endpoint POST /api/v1/reconciliation/monitor/.
        """
        self.vpn_access.enable()
        self.client.force_authenticate(user=self.admin_user)

        monitor_url = "/api/v1/reconciliation/monitor/"
        response = self.client.post(monitor_url, {
            "employee_id": str(self.employee.id),
            "auto_approve": True
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['system_status'], 'CONSISTENT')
        self.assertEqual(response.data['repairs_executed_count'], 1)

        self.vpn_access.refresh_from_db()
        self.assertEqual(self.vpn_access.status, VPNAccessStatus.DISABLED)

    def test_full_fleet_continuous_monitoring_cycle(self):
        """
        Regression test: Verify that calling run_monitoring_cycle() without employee_id
        evaluates all employees across the fleet without raising AttributeError.
        """
        # Create a second employee with drift to ensure multi-employee evaluation
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

        # Re-enable VPN for Rahul to create drift
        self.vpn_access.enable()

        summary = self.monitor.run_monitoring_cycle(auto_approve_policy=True)

        self.assertIsInstance(summary, dict)
        self.assertEqual(summary['employees_evaluated_count'], 2)
        self.assertEqual(summary['violations_detected_count'], 2)
        self.assertEqual(summary['repair_plans_generated_count'], 2)
        self.assertEqual(summary['approvals_processed_count'], 2)
        self.assertEqual(summary['repairs_executed_count'], 2)
        self.assertEqual(summary['verifications_completed_count'], 2)
        self.assertEqual(summary['remaining_open_violations_count'], 0)
        self.assertEqual(summary['system_status'], 'CONSISTENT')

