"""
Django management command to generate Repair Plans for detected integrity violations.
"""

import json
from django.core.management.base import BaseCommand
from apps.workflows.planner import RepairPlanner
from apps.employees.models import Employee


class Command(BaseCommand):
    help = 'Generates safe, deterministic repair plans for active integrity violations without executing repair actions.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Specific employee email to evaluate for repair planning.'
        )

    def handle(self, *args, **options):
        email = options.get('email')
        planner = RepairPlanner()

        self.stdout.write(self.style.MIGRATE_HEADING("=== ReconcileOS Repair Planning Engine ==="))

        employee_id = None
        if email:
            try:
                emp = Employee.objects.get(email=email)
                employee_id = str(emp.id)
            except Employee.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Employee with email '{email}' not found."))
                return

        plans = planner.plan_all_open_violations(employee_id=employee_id)

        self.stdout.write(self.style.SUCCESS(f"\nGenerated/Retrieved {len(plans)} Repair Plan(s):"))

        plan_data = []
        for plan in plans:
            plan_dict = {
                "id": str(plan.id),
                "employee": f"{plan.employee.full_name} ({plan.employee.email})",
                "violation_id": str(plan.violation_id),
                "target_system": plan.target_system,
                "action": plan.action,
                "reason": plan.reason,
                "risk_level": plan.risk_level,
                "sensitivity_level": plan.sensitivity_level,
                "status": plan.status,
                "created_at": plan.created_at.isoformat(),
                "updated_at": plan.updated_at.isoformat()
            }
            plan_data.append(plan_dict)

        self.stdout.write(json.dumps(plan_data, indent=2))
