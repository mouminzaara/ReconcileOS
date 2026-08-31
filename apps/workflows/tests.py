"""
Unit tests for ReconcileOS Repair Planning Engine (Milestone 7).
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
from apps.workflows.models import RepairPlan, PlanStatus
from apps.workflows.planner import RepairPlanner


class RepairPlanningTestCase(TestCase):
    """
    Test suite for Repair Planning Engine models, planner logic, and API.
    """

    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser('admin_plan', 'admin@plan.com', 'admin123')
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

        self.reconciliation_engine = ReconciliationEngine()
        self.reconciliation_report = self.reconciliation_engine.evaluate_employee_rules(str(self.employee.id))
        self.violation = IntegrityViolation.objects.get(employee=self.employee, status=ViolationStatus.OPEN)

    def test_integrity_violation_created_for_rahul(self):
        """
        Verify that reconciliation engine detected authorization drift for Rahul Kumar.
        """
        self.assertEqual(self.violation.affected_system, 'VPN')
        self.assertEqual(self.violation.expected_state, 'DISABLED')
        self.assertEqual(self.violation.actual_state, 'ENABLED')
        self.assertEqual(self.violation.status, ViolationStatus.OPEN)

    def test_deterministic_repair_plan_generation_for_rahul(self):
        """
        Verify that RepairPlanner produces the exact expected repair plan for Rahul Kumar:
        Action: DISABLE VPN ACCESS
        Target System: VPN
        Status: PENDING
        """
        planner = RepairPlanner()
        plan, created = planner.plan_for_violation(self.violation)

        self.assertTrue(created)
        self.assertIsNotNone(plan.id)
        self.assertEqual(plan.employee, self.employee)
        self.assertEqual(plan.violation, self.violation)
        self.assertEqual(plan.target_system, 'VPN')
        self.assertEqual(plan.action, 'DISABLE VPN ACCESS')
        self.assertEqual(plan.risk_level, RuleSeverity.CRITICAL)
        self.assertEqual(plan.sensitivity_level, RuleSeverity.CRITICAL)
        self.assertEqual(plan.status, PlanStatus.PENDING)
        self.assertIn('Rahul Kumar', plan.reason)
        self.assertIn('TERMINATED', plan.reason)
        self.assertIn('ENABLED', plan.reason)
        self.assertIsNotNone(plan.created_at)
        self.assertIsNotNone(plan.updated_at)

    def test_prevent_duplicate_active_repair_plans(self):
        """
        Verify that calling RepairPlanner multiple times for the same unresolved violation
        returns the existing active plan and does NOT create duplicate records.
        """
        planner = RepairPlanner()

        plan1, created1 = planner.plan_for_violation(self.violation)
        self.assertTrue(created1)

        plan2, created2 = planner.plan_for_violation(self.violation)
        self.assertFalse(created2)
        self.assertEqual(plan1.id, plan2.id)

        active_plans_count = RepairPlan.objects.filter(violation=self.violation).count()
        self.assertEqual(active_plans_count, 1)

    def test_plan_statuses_choices(self):
        """
        Verify all required plan status choices exist in PlanStatus.
        """
        expected_statuses = {'PENDING', 'APPROVED', 'REJECTED', 'EXECUTING', 'COMPLETED', 'FAILED'}
        defined_statuses = set(PlanStatus.values)
        self.assertTrue(expected_statuses.issubset(defined_statuses))

    def test_vpn_access_remains_enabled_after_planning(self):
        """
        Verify that generating a repair plan does NOT execute repair actions
        and VPN access remains ENABLED.
        """
        planner = RepairPlanner()
        plan, _ = planner.plan_for_violation(self.violation)

        self.vpn_access.refresh_from_db()
        self.assertEqual(self.vpn_access.status, VPNAccessStatus.ENABLED)
        self.assertEqual(plan.status, PlanStatus.PENDING)

    def test_generate_repair_plans_management_command(self):
        """
        Test execution of generate_repair_plans management command.
        """
        out = StringIO()
        call_command('generate_repair_plans', '--email', 'rahul.kumar@company.com', stdout=out)
        output = out.getvalue()

        self.assertIn("Generated/Retrieved 1 Repair Plan(s)", output)
        self.assertIn("DISABLE VPN ACCESS", output)
        self.assertIn("rahul.kumar@company.com", output)

    def test_repair_plan_api_list_and_generate(self):
        """
        Test API endpoints GET /api/v1/workflows/plans/ and POST /api/v1/workflows/plans/generate/.
        """
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post('/api/v1/workflows/plans/generate/', {'employee_id': str(self.employee.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['action'], 'DISABLE VPN ACCESS')

        response = self.client.get('/api/v1/workflows/plans/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['target_system'], 'VPN')
        self.assertEqual(response.data['results'][0]['status'], 'PENDING')
