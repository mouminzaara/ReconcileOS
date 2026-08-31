"""
Management command to execute Continuous Integrity Monitoring cycles.
"""

import json
import time
import logging
from django.core.management.base import BaseCommand
from apps.reconciliation.monitor import ContinuousMonitor

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Executes continuous integrity monitoring cycles to detect drift and drive self-healing.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--once',
            action='store_true',
            help='Run a single monitoring cycle and exit.'
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=0,
            help='Interval in seconds between continuous monitoring cycles (default: 0 for single run).'
        )
        parser.add_argument(
            '--employee-id',
            type=str,
            default=None,
            help='Target specific employee UUID for monitoring audit.'
        )
        parser.add_argument(
            '--auto-approve',
            action='store_true',
            help='Automatically approve repair plans generated during the monitoring cycle according to policy.'
        )

    def handle(self, *args, **options):
        once = options['once']
        interval = options['interval']
        employee_id = options['employee_id']
        auto_approve = options['auto_approve']

        monitor = ContinuousMonitor()

        self.stdout.write(self.style.SUCCESS("=== ReconcileOS Continuous Integrity Monitor ==="))

        if once or interval == 0:
            self.stdout.write("Executing single monitoring cycle...")
            summary = monitor.run_monitoring_cycle(
                employee_id=employee_id,
                auto_approve_policy=auto_approve
            )
            self.stdout.write(json.dumps(summary, indent=2))
            if summary['system_status'] == 'CONSISTENT':
                self.stdout.write(self.style.SUCCESS(f"\n[MONITORING COMPLETE] System is CONSISTENT (0 open violations)."))
            else:
                self.stdout.write(self.style.WARNING(f"\n[MONITORING COMPLETE] System has DRIFT DETECTED ({summary['remaining_open_violations_count']} open violations)."))
        else:
            self.stdout.write(f"Starting continuous monitoring loop (interval: {interval} seconds)...")
            try:
                cycle_count = 0
                while True:
                    cycle_count += 1
                    self.stdout.write(f"\n--- Monitoring Cycle #{cycle_count} ---")
                    summary = monitor.run_monitoring_cycle(
                        employee_id=employee_id,
                        auto_approve_policy=auto_approve
                    )
                    self.stdout.write(json.dumps(summary, indent=2))
                    time.sleep(interval)
            except KeyboardInterrupt:
                self.stdout.write(self.style.SUCCESS("\nContinuous monitoring loop stopped by user."))
