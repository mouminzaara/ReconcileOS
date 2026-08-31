"""
Django management command to execute Post-Repair Empirical Verification via CLI.
"""

import json
from django.core.management.base import BaseCommand
from apps.workflows.models import RepairPlan
from apps.workflows.verifier import PostRepairVerifier


class Command(BaseCommand):
    help = 'Re-queries target downstream system state to empirically verify post-repair consistency.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--plan-id',
            type=str,
            required=True,
            help='UUID of the repair plan to verify.'
        )

    def handle(self, *args, **options):
        plan_id = options.get('plan_id')
        verifier = PostRepairVerifier()

        self.stdout.write(self.style.MIGRATE_HEADING("=== ReconcileOS Post-Repair Verification Engine ==="))

        try:
            plan = RepairPlan.objects.get(pk=plan_id)
        except RepairPlan.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Repair plan with ID '{plan_id}' does not exist."))
            return

        verification = verifier.verify_repair(plan)
        plan.refresh_from_db()

        if verification.result == 'VERIFIED':
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n[VERIFICATION SUCCESS] Repair Plan {plan.id} is VERIFIED (State Consistent). "
                    f"Plan Status: {plan.status}, Violation Status: {plan.violation.status}."
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    f"\n[VERIFICATION FAILED] Repair Plan {plan.id} failed verification: {verification.details}"
                )
            )

        self.stdout.write(json.dumps({
            "verification_id": str(verification.id),
            "plan_id": str(plan.id),
            "employee": plan.employee.full_name,
            "target_system": plan.target_system,
            "expected_state": verification.expected_state,
            "actual_state": verification.actual_state,
            "result": verification.result,
            "plan_status": plan.status,
            "violation_status": plan.violation.status,
            "details": verification.details,
            "verified_at": verification.verified_at.isoformat() if verification.verified_at else None
        }, indent=2))
