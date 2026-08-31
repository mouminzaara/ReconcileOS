"""
Django management command to seed initial invariant security rules for ReconcileOS.
"""

from django.core.management.base import BaseCommand
from apps.rules.models import Rule, RuleSeverity


class Command(BaseCommand):
    help = 'Seeds initial invariant rules for ReconcileOS integrity checks.'

    def handle(self, *args, **options):
        initial_rules = [
            {
                "rule_code": "INV-RULE-001",
                "name": "Terminated employees must not have VPN access",
                "description": (
                    "Whenever an employee's HR status transitions to TERMINATED, "
                    "their downstream VPN access status must be set to DISABLED."
                ),
                "source_system": "HR",
                "condition_attribute": "status",
                "condition_value": "TERMINATED",
                "target_system": "VPN",
                "expected_attribute": "status",
                "expected_value": "DISABLED",
                "severity": RuleSeverity.CRITICAL,
                "is_enabled": True
            },
            {
                "rule_code": "INV-RULE-002",
                "name": "Terminated employees must not retain GitHub organization membership",
                "description": (
                    "Terminated employees must be unassigned from all enterprise "
                    "GitHub organizations and private repository permissions."
                ),
                "source_system": "HR",
                "condition_attribute": "status",
                "condition_value": "TERMINATED",
                "target_system": "GitHub",
                "expected_attribute": "status",
                "expected_value": "REVOKED",
                "severity": RuleSeverity.HIGH,
                "is_enabled": True
            },
            {
                "rule_code": "INV-RULE-003",
                "name": "Terminated employees must not retain Cloud IAM roles",
                "description": (
                    "Terminated employees must have all assigned Cloud IAM role permissions "
                    "and policies revoked to prevent unauthorized infrastructure access."
                ),
                "source_system": "HR",
                "condition_attribute": "status",
                "condition_value": "TERMINATED",
                "target_system": "Cloud",
                "expected_attribute": "access_status",
                "expected_value": "NO_ROLE",
                "severity": RuleSeverity.CRITICAL,
                "is_enabled": True
            },
            {
                "rule_code": "INV-RULE-004",
                "name": "Terminated employees must not retain active Slack accounts",
                "description": (
                    "Terminated employees must have their enterprise Slack workspace account "
                    "deactivated immediately upon offboarding."
                ),
                "source_system": "HR",
                "condition_attribute": "status",
                "condition_value": "TERMINATED",
                "target_system": "Slack",
                "expected_attribute": "access_status",
                "expected_value": "DEACTIVATED",
                "severity": RuleSeverity.HIGH,
                "is_enabled": True
            }
        ]

        created_count = 0
        updated_count = 0

        for r_data in initial_rules:
            rule, created = Rule.objects.get_or_create(
                rule_code=r_data['rule_code'],
                defaults=r_data
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created Rule: {rule.rule_code} — {rule.name}"))
            else:
                for key, val in r_data.items():
                    setattr(rule, key, val)
                rule.save()
                updated_count += 1
                self.stdout.write(self.style.WARNING(f"Updated Rule: {rule.rule_code} — {rule.name}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Rule seeding completed. {created_count} created, {updated_count} verified/updated."
            )
        )
