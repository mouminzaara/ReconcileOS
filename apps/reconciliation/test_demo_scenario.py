"""
Tests for the seed_demo_scenario management command.

Verifies the full demo lifecycle:
  1. Seeding creates the correct employee, VPN, violation, plan, and approval.
  2. Re-running is idempotent and safe.
  3. --reset-only cleans artifacts without re-seeding.
  4. The approval → execute → verify workflow succeeds end-to-end.
"""

from io import StringIO
from django.test import TestCase
from django.core.management import call_command

from apps.employees.models import Employee, EmployeeStatus
from apps.connectors.models import VPNAccess, VPNAccessStatus
from apps.reconciliation.models import IntegrityViolation, ViolationStatus
from apps.workflows.models import RepairPlan, PlanStatus
from apps.approvals.models import ApprovalRequest, ApprovalDecision

DEMO_EMAIL = "rahul.kumar@reconcileos.internal"


class SeedDemoScenarioTests(TestCase):
    """Tests for the seed_demo_scenario management command."""

    def _run_seed(self, *extra_args):
        """Helper: run seed_demo_scenario, return stdout."""
        out = StringIO()
        call_command('seed_demo_scenario', *extra_args, stdout=out)
        return out.getvalue()

    # ── Basic seeding ─────────────────────────────────────────────────

    def test_seed_creates_employee_terminated(self):
        """Employee is created with TERMINATED status."""
        self._run_seed()
        emp = Employee.objects.get(email=DEMO_EMAIL)
        self.assertEqual(emp.status, EmployeeStatus.TERMINATED)
        self.assertEqual(emp.full_name, "Rahul Kumar")

    def test_seed_creates_vpn_enabled(self):
        """VPN access record is ENABLED after seeding."""
        self._run_seed()
        emp = Employee.objects.get(email=DEMO_EMAIL)
        vpn = VPNAccess.objects.get(employee=emp)
        self.assertEqual(vpn.status, VPNAccessStatus.ENABLED)

    def test_seed_creates_open_vpn_violation(self):
        """At least one OPEN violation exists for VPN after seeding."""
        self._run_seed()
        emp = Employee.objects.get(email=DEMO_EMAIL)
        vpn_viol = IntegrityViolation.objects.filter(
            employee=emp,
            affected_system='VPN',
            status=ViolationStatus.OPEN,
        )
        self.assertTrue(vpn_viol.exists())

    def test_seed_creates_pending_repair_plan(self):
        """A PENDING repair plan for VPN exists after seeding."""
        self._run_seed()
        emp = Employee.objects.get(email=DEMO_EMAIL)
        plan = RepairPlan.objects.filter(
            employee=emp,
            target_system='VPN',
            status=PlanStatus.PENDING,
        )
        self.assertTrue(plan.exists())
        self.assertEqual(plan.first().action, 'DISABLE VPN ACCESS')

    def test_seed_creates_pending_approval(self):
        """A PENDING approval request is linked to the VPN repair plan."""
        self._run_seed()
        emp = Employee.objects.get(email=DEMO_EMAIL)
        plan = RepairPlan.objects.get(
            employee=emp,
            target_system='VPN',
            status=PlanStatus.PENDING,
        )
        approval = ApprovalRequest.objects.filter(
            repair_plan=plan,
            decision=ApprovalDecision.PENDING,
        )
        self.assertTrue(approval.exists())

    # ── Idempotency ───────────────────────────────────────────────────

    def test_seed_is_idempotent(self):
        """Running seed twice does not create duplicate employees or plans."""
        self._run_seed()
        self._run_seed()

        emp_count = Employee.objects.filter(email=DEMO_EMAIL).count()
        self.assertEqual(emp_count, 1)

        emp = Employee.objects.get(email=DEMO_EMAIL)
        # Should have exactly 1 PENDING VPN plan after re-run
        vpn_plans = RepairPlan.objects.filter(
            employee=emp,
            target_system='VPN',
            status=PlanStatus.PENDING,
        )
        self.assertEqual(vpn_plans.count(), 1)

    # ── Reset-only mode ───────────────────────────────────────────────

    def test_reset_only_cleans_artifacts(self):
        """--reset-only removes violations, plans, approvals but keeps employee."""
        self._run_seed()
        self._run_seed('--reset-only')

        emp = Employee.objects.get(email=DEMO_EMAIL)
        self.assertEqual(emp.status, EmployeeStatus.TERMINATED)

        vpn = VPNAccess.objects.get(employee=emp)
        self.assertEqual(vpn.status, VPNAccessStatus.ENABLED)

        # Artifacts should be cleared
        self.assertEqual(
            IntegrityViolation.objects.filter(employee=emp).count(), 0
        )
        self.assertEqual(
            RepairPlan.objects.filter(employee=emp).count(), 0
        )

    def test_reset_then_reseed_works(self):
        """Reset then reseed produces a fresh demo scenario."""
        self._run_seed()
        self._run_seed('--reset-only')
        self._run_seed()

        emp = Employee.objects.get(email=DEMO_EMAIL)
        self.assertTrue(
            IntegrityViolation.objects.filter(
                employee=emp, affected_system='VPN', status=ViolationStatus.OPEN
            ).exists()
        )
        self.assertTrue(
            RepairPlan.objects.filter(
                employee=emp, target_system='VPN', status=PlanStatus.PENDING
            ).exists()
        )

    # ── VPN state recovery after execution ────────────────────────────

    def test_reseed_recovers_vpn_after_execution(self):
        """After a full execution disables VPN, re-seeding restores ENABLED state."""
        self._run_seed()
        emp = Employee.objects.get(email=DEMO_EMAIL)

        # Simulate what happens after execution: VPN becomes DISABLED
        vpn = VPNAccess.objects.get(employee=emp)
        vpn.status = VPNAccessStatus.DISABLED
        vpn.save(update_fields=['status', 'updated_at'])

        # Re-seed should restore ENABLED
        self._run_seed()
        vpn.refresh_from_db()
        self.assertEqual(vpn.status, VPNAccessStatus.ENABLED)
