"""
Django management command to collect and display multi-system identity state.
"""

import json
from django.core.management.base import BaseCommand
from apps.reconciliation.collectors import StateCollector, EmployeeNotFoundException, InvalidEmployeeIDException


class Command(BaseCommand):
    help = 'Collects multi-system identity state from HR and connected applications.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Specific employee email to collect state for (default: Rahul Kumar / all).'
        )

    def handle(self, *args, **options):
        target_email = options.get('email') or "rahul.kumar@reconcileos.internal"
        collector = StateCollector()

        self.stdout.write(self.style.MIGRATE_HEADING("=== ReconcileOS State Collection Engine ==="))

        try:
            state_payload = collector.collect_employee_state(target_email)
            self.stdout.write(self.style.SUCCESS(f"\nCollected State Payload for '{target_email}':"))
            self.stdout.write(json.dumps(state_payload, indent=2))
        except (EmployeeNotFoundException, InvalidEmployeeIDException) as exc:
            self.stdout.write(self.style.WARNING(f"Target '{target_email}' not found. Collecting all states instead:\n"))
            all_states = collector.collect_all_states()
            self.stdout.write(json.dumps(all_states, indent=2))
