"""
Django management command: seed_demo_scenario

Prepares a complete, repeatable demonstration scenario for ReconcileOS:

Story: Employee "Rahul Kumar" is TERMINATED in HR but still has ENABLED VPN access.
       ReconcileOS detects the drift, proposes "DISABLE VPN ACCESS", and creates
       a PENDING approval request waiting for human action.

Steps performed:
  1. Ensure invariant rules exist (idempotent, calls seed_rules logic).
  2. Ensure demo employee "Rahul Kumar" exists as TERMINATED.
  3. Ensure VPN access record exists as ENABLED.
  4. Clean up any prior demo violations, repair plans, and approval requests
     for this specific employee only (does NOT delete audit logs or other data).
  5. Run ReconciliationEngine to detect the VPN drift violation.
  6. Run RepairPlanner to generate a PENDING repair plan (which auto-creates
     a PENDING ApprovalRequest via ApprovalService).
  7. Print summary and stop — no approval, no execution.

Safe to run multiple times; idempotent on employee/connector state and
cleans prior demo workflow artifacts to avoid duplicates.
"""

import json
from django.core.management.base import BaseCommand
from django.core.management import call_command
from apps.employees.models import Employee, EmployeeStatus
from apps.connectors.models import VPNAccess, VPNAccessStatus
from apps.reconciliation.engine import ReconciliationEngine
from apps.reconciliation.models import IntegrityViolation, ViolationStatus
from apps.workflows.planner import RepairPlanner
from apps.workflows.models import RepairPlan, PlanStatus
from apps.approvals.models import ApprovalRequest, ApprovalDecision

# Fixed demo identity — always the same employee for repeatability
DEMO_EMAIL = "rahul.kumar@reconcileos.internal"
DEMO_FULL_NAME = "Rahul Kumar"
DEMO_DEPARTMENT = "DevOps & Cloud Integrity"


class Command(BaseCommand):
    help = (
        "Seeds a complete demo scenario: terminated employee with enabled VPN access, "
        "detected violation, pending repair plan, and pending approval request. "
        "Safe to run repeatedly."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset-only',
            action='store_true',
            help=(
                'Only clean up prior demo workflow artifacts (violations, plans, '
                'approvals) for the demo employee without re-seeding. Leaves the '
                'employee and VPN records intact.'
            ),
        )

    def handle(self, *args, **options):
        reset_only = options.get('reset_only', False)

        self.stdout.write(self.style.MIGRATE_HEADING(
            "\n=================================================="
        ))
        self.stdout.write(self.style.MIGRATE_HEADING(
            "  ReconcileOS -- Demo Scenario Seeder"
        ))
        self.stdout.write(self.style.MIGRATE_HEADING(
            "==================================================\n"
        ))

        # ── Step 1: Ensure invariant rules exist ──────────────────────
        self.stdout.write("  [1/6] Ensuring invariant rules exist...")
        call_command('seed_rules', stdout=self.stdout)

        # ── Step 2: Ensure demo employee exists as TERMINATED ─────────
        self.stdout.write("\n  [2/6] Ensuring demo employee exists (TERMINATED)...")
        employee, emp_created = Employee.objects.get_or_create(
            email=DEMO_EMAIL,
            defaults={
                "full_name": DEMO_FULL_NAME,
                "department": DEMO_DEPARTMENT,
                "status": EmployeeStatus.TERMINATED,
            }
        )
        if not emp_created:
            changed = False
            if employee.full_name != DEMO_FULL_NAME:
                employee.full_name = DEMO_FULL_NAME
                changed = True
            if employee.department != DEMO_DEPARTMENT:
                employee.department = DEMO_DEPARTMENT
                changed = True
            if employee.status != EmployeeStatus.TERMINATED:
                employee.status = EmployeeStatus.TERMINATED
                changed = True
            if changed:
                employee.save()
                self.stdout.write(self.style.WARNING(
                    f"    Updated existing employee to TERMINATED: {employee}"
                ))
            else:
                self.stdout.write(f"    Already exists: {employee}")
        else:
            self.stdout.write(self.style.SUCCESS(
                f"    Created: {employee}"
            ))

        # ── Step 3: Ensure VPN access is ENABLED ──────────────────────
        self.stdout.write("\n  [3/6] Ensuring VPN access is ENABLED...")
        vpn_access, vpn_created = VPNAccess.objects.get_or_create(
            employee=employee,
            defaults={"status": VPNAccessStatus.ENABLED}
        )
        if not vpn_created and vpn_access.status != VPNAccessStatus.ENABLED:
            vpn_access.status = VPNAccessStatus.ENABLED
            vpn_access.save(update_fields=['status', 'updated_at'])
            self.stdout.write(self.style.WARNING(
                f"    Reset VPN access to ENABLED for {employee.full_name}"
            ))
        elif vpn_created:
            self.stdout.write(self.style.SUCCESS(
                f"    Created VPN access (ENABLED) for {employee.full_name}"
            ))
        else:
            self.stdout.write(
                f"    VPN access already ENABLED for {employee.full_name}"
            )

        # ── Step 4: Clean up prior demo workflow artifacts ────────────
        self.stdout.write("\n  [4/6] Cleaning prior demo artifacts for this employee...")
        # Delete approval requests linked to this employee's repair plans
        demo_plans = RepairPlan.objects.filter(employee=employee)
        approvals_deleted, _ = ApprovalRequest.objects.filter(
            repair_plan__in=demo_plans
        ).delete()
        # Delete repair plans for this employee
        plans_deleted, _ = demo_plans.delete()
        # Delete open violations for this employee
        violations_deleted, _ = IntegrityViolation.objects.filter(
            employee=employee
        ).delete()

        self.stdout.write(
            f"    Removed: {violations_deleted} violation(s), "
            f"{plans_deleted} plan(s), {approvals_deleted} approval(s)"
        )

        if reset_only:
            self.stdout.write(self.style.SUCCESS(
                "\n  [OK] Reset complete. Demo artifacts cleaned. "
                "Run without --reset-only to re-seed.\n"
            ))
            return

        # ── Step 5: Run reconciliation to detect the violation ────────
        self.stdout.write("\n  [5/6] Running reconciliation engine...")
        engine = ReconciliationEngine()
        report = engine.evaluate_employee_rules(employee)

        violations_found = report.get('violations_detected_count', 0)
        self.stdout.write(
            f"    Rules evaluated: {report.get('rules_evaluated_count', 0)}"
        )
        self.stdout.write(
            f"    Violations detected: {violations_found}"
        )

        if violations_found == 0:
            self.stdout.write(self.style.ERROR(
                "\n  [FAIL] No violations detected. Check that INV-RULE-001 is enabled "
                "and employee status is TERMINATED with VPN ENABLED.\n"
            ))
            return

        # Show detected violations
        for v_data in report.get('violations', []):
            self.stdout.write(self.style.WARNING(
                f"    > {v_data['rule_code']}: {v_data['affected_system']} "
                f"(Expected: {v_data['expected_state']}, "
                f"Actual: {v_data['actual_state']}) [{v_data['severity']}]"
            ))

        # ── Step 6: Generate repair plans (auto-creates approvals) ────
        self.stdout.write("\n  [6/6] Generating repair plans & approval requests...")
        planner = RepairPlanner()
        plans = planner.plan_all_open_violations(employee_id=str(employee.id))

        for plan in plans:
            approval = ApprovalRequest.objects.filter(
                repair_plan=plan,
                decision=ApprovalDecision.PENDING,
            ).first()
            self.stdout.write(self.style.SUCCESS(
                f"    > Plan: {plan.action} [{plan.status}] "
                f"(Risk: {plan.risk_level})"
            ))
            if approval:
                self.stdout.write(self.style.SUCCESS(
                    f"      Approval: {approval.id} [{approval.decision}]"
                ))

        # -- Summary -------------------------------------------------------
        vpn_violation = IntegrityViolation.objects.filter(
            employee=employee,
            affected_system='VPN',
            status=ViolationStatus.OPEN,
        ).first()

        vpn_plan = RepairPlan.objects.filter(
            employee=employee,
            target_system='VPN',
            status=PlanStatus.PENDING,
        ).first()

        vpn_approval = None
        if vpn_plan:
            vpn_approval = ApprovalRequest.objects.filter(
                repair_plan=vpn_plan,
                decision=ApprovalDecision.PENDING,
            ).first()

        self.stdout.write(self.style.MIGRATE_HEADING(
            "\n=================================================="
        ))
        self.stdout.write(self.style.MIGRATE_HEADING(
            "  DEMO SCENARIO READY"
        ))
        self.stdout.write(self.style.MIGRATE_HEADING(
            "=================================================="
        ))
        self.stdout.write(
            f"\n  Employee : {employee.full_name} ({employee.email})\n"
            f"  HR Status: {employee.status}\n"
            f"  VPN State: {vpn_access.status}\n"
            f"\n"
            f"  VPN Violation  : {vpn_violation.id if vpn_violation else 'None'}\n"
            f"  VPN Repair Plan: {vpn_plan.id if vpn_plan else 'None'} [{vpn_plan.status if vpn_plan else ''}]\n"
            f"  Approval Req   : {vpn_approval.id if vpn_approval else 'None'} [{vpn_approval.decision if vpn_approval else ''}]\n"
            f"\n"
            f"  +---------------------------------------------+\n"
            f"  | NEXT: Open the browser and demonstrate:     |\n"
            f"  |  1. Dashboard -> see violation count        |\n"
            f"  |  2. Violations -> see OPEN VPN drift        |\n"
            f"  |  3. Repairs -> see PENDING repair plan      |\n"
            f"  |  4. Approvals -> APPROVE the request        |\n"
            f"  |  5. Repairs -> EXECUTE the approved plan    |\n"
            f"  |  6. Audit Logs -> see full event trail      |\n"
            f"  |  7. Violations -> confirm RESOLVED          |\n"
            f"  +---------------------------------------------+\n"
        )
