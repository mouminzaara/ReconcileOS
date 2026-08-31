"""
Django management command to seed the multi-system demonstration scenario for ReconcileOS:
Authorization Drift State across HR, VPN, GitHub, Cloud IAM, and Slack.
"""

from django.core.management.base import BaseCommand
from apps.employees.models import Employee, EmployeeStatus
from apps.connectors.models import (
    VPNAccess, VPNAccessStatus,
    GitHubMembership, GitHubAccessStatus,
    CloudIAMAccess, CloudRole,
    SlackAccount, SlackAccountStatus
)


class Command(BaseCommand):
    help = (
        'Seeds or updates the multi-system demonstration scenario for authorization drift: '
        'Rahul Kumar (HR: TERMINATED, VPN: ENABLED, GitHub: MEMBER, Cloud: DEVELOPER_ROLE, Slack: ACTIVE).'
    )

    def handle(self, *args, **options):
        email = "rahul.kumar@reconcileos.internal"
        full_name = "Rahul Kumar"
        department = "DevOps & Cloud Integrity"

        # 1. HR Record: TERMINATED
        employee, _ = Employee.objects.get_or_create(
            email=email,
            defaults={
                "full_name": full_name,
                "department": department,
                "status": EmployeeStatus.TERMINATED
            }
        )
        if employee.status != EmployeeStatus.TERMINATED:
            employee.status = EmployeeStatus.TERMINATED
            employee.save(update_fields=['status', 'updated_at'])

        # 2. VPN Access: ENABLED
        vpn_access, _ = VPNAccess.objects.get_or_create(
            employee=employee,
            defaults={"status": VPNAccessStatus.ENABLED}
        )
        if vpn_access.status != VPNAccessStatus.ENABLED:
            vpn_access.status = VPNAccessStatus.ENABLED
            vpn_access.save(update_fields=['status', 'updated_at'])

        # 3. GitHub Membership: MEMBER
        gh_membership, _ = GitHubMembership.objects.get_or_create(
            employee=employee,
            defaults={
                "github_username": "rahulkumar_gh",
                "org_name": "reconcileos-org",
                "status": GitHubAccessStatus.MEMBER
            }
        )
        if gh_membership.status != GitHubAccessStatus.MEMBER:
            gh_membership.status = GitHubAccessStatus.MEMBER
            gh_membership.save(update_fields=['status', 'updated_at'])

        # 4. Cloud IAM Access: DEVELOPER_ROLE
        cloud_access, _ = CloudIAMAccess.objects.get_or_create(
            employee=employee,
            defaults={
                "cloud_identity": f"arn:aws:iam::123456789012:user/{employee.email.split('@')[0]}",
                "role": CloudRole.DEVELOPER_ROLE
            }
        )
        if cloud_access.role != CloudRole.DEVELOPER_ROLE:
            cloud_access.role = CloudRole.DEVELOPER_ROLE
            cloud_access.save(update_fields=['role', 'updated_at'])

        # 5. Slack Account: ACTIVE
        slack_account, _ = SlackAccount.objects.get_or_create(
            employee=employee,
            defaults={
                "slack_user_id": "U10293847",
                "status": SlackAccountStatus.ACTIVE
            }
        )
        if slack_account.status != SlackAccountStatus.ACTIVE:
            slack_account.status = SlackAccountStatus.ACTIVE
            slack_account.save(update_fields=['status', 'updated_at'])

        # Output Summary
        self.stdout.write(self.style.MIGRATE_HEADING("=== ReconcileOS Multi-System Demo Scenario Seeder ==="))
        self.stdout.write(
            self.style.NOTICE(
                "\n[DRIFT DEMO SCENARIO INITIALIZED]\n"
                f"Employee : {employee.full_name} ({employee.id})\n"
                f"HR State : {employee.status} (Terminated in HR system)\n"
                f"VPN      : {vpn_access.status}\n"
                f"GitHub   : {gh_membership.status} ({gh_membership.github_username})\n"
                f"Cloud IAM: {cloud_access.role}\n"
                f"Slack    : {slack_account.status}\n"
                "Result   : 4 MULTI-SYSTEM AUTHORIZATION DRIFT VIOLATIONS PREPARED"
            )
        )
