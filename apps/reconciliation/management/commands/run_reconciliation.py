"""
Django management command to execute ReconcileOS Reconciliation Engine audit check.
"""

import json
from django.core.management.base import BaseCommand
from apps.reconciliation.engine import ReconciliationEngine
from apps.reconciliation.collectors import EmployeeNotFoundException, InvalidEmployeeIDException


class Command(BaseCommand):
    help = 'Executes ReconcileOS reconciliation audit check comparing expected vs actual states.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Specific employee email to evaluate (default: all employees).'
        )

    def handle(self, *args, **options):
        target_email = options.get('email')
        engine = ReconciliationEngine()

        self.stdout.write(self.style.MIGRATE_HEADING("=== ReconcileOS Reconciliation Engine ==="))

        if target_email:
            try:
                report = engine.evaluate_employee_rules(target_email)
                self.stdout.write(self.style.SUCCESS(f"\nReconciliation Report for '{target_email}':"))
                self.stdout.write(json.dumps(report, indent=2))
            except (EmployeeNotFoundException, InvalidEmployeeIDException) as exc:
                self.stdout.write(self.style.ERROR(f"Error: {exc}"))
        else:
            reports = engine.evaluate_all()
            total_viols = sum(r['violations_detected_count'] for r in reports)
            self.stdout.write(self.style.SUCCESS(f"\nReconciliation Audit Completed for {len(reports)} Employee(s):"))
            self.stdout.write(self.style.WARNING(f"Total Active Violations Detected: {total_viols}\n"))
            self.stdout.write(json.dumps(reports, indent=2))
