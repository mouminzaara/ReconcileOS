"""
Django management command to execute approved Repair Plans via CLI.
"""

import json
from django.core.management.base import BaseCommand
from apps.workflows.models import RepairPlan
from apps.workflows.executor import RepairExecutor, IneligiblePlanExecutionException, ExecutionException


class Command(BaseCommand):
    help = 'Executes an approved RepairPlan against its target connector.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--plan-id',
            type=str,
            required=True,
            help='UUID of the approved repair plan to execute.'
        )

    def handle(self, *args, **options):
        plan_id = options.get('plan_id')
        executor = RepairExecutor()

        self.stdout.write(self.style.MIGRATE_HEADING("=== ReconcileOS Repair Execution Engine ==="))

        try:
            plan = RepairPlan.objects.get(pk=plan_id)
        except RepairPlan.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Repair plan with ID '{plan_id}' does not exist."))
            return
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"Invalid plan ID '{plan_id}': {exc}"))
            return

        try:
            log = executor.execute_plan(plan)
            plan.refresh_from_db()

            if log.status == 'SUCCESS':
                self.stdout.write(
                    self.style.SUCCESS(
                        f"\n[EXECUTION SUCCESS] Repair Plan {plan.id} [{plan.action}] for {plan.employee.full_name} completed."
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"\n[EXECUTION FAILED] Repair Plan {plan.id} failed: {log.error_details}"
                    )
                )

            self.stdout.write(json.dumps({
                "plan_id": str(plan.id),
                "employee": plan.employee.full_name,
                "target_system": plan.target_system,
                "action": plan.action,
                "plan_status": plan.status,
                "execution_log_id": str(log.id),
                "execution_status": log.status,
                "output_message": log.output_message,
                "error_details": log.error_details,
                "started_at": log.started_at.isoformat(),
                "completed_at": log.completed_at.isoformat() if log.completed_at else None
            }, indent=2))

        except (IneligiblePlanExecutionException, ExecutionException) as exc:
            self.stdout.write(self.style.ERROR(f"Execution Error: {exc}"))
