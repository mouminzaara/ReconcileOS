"""
Connector models for downstream connected systems (VPN, GitHub, Cloud IAM, Slack).
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class VPNAccessStatus(models.TextChoices):
    """
    Status of an employee's access to the enterprise VPN.
    """
    ENABLED = 'ENABLED', _('Enabled')
    DISABLED = 'DISABLED', _('Disabled')


class VPNAccess(models.Model):
    """
    Represents the current VPN access state for an employee in the downstream VPN system.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_("Unique identifier for the VPN access record (UUIDv4).")
    )
    employee = models.OneToOneField(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='vpn_access',
        help_text=_("Associated employee in the primary HR system of record.")
    )
    status = models.CharField(
        max_length=20,
        choices=VPNAccessStatus.choices,
        default=VPNAccessStatus.DISABLED,
        db_index=True,
        help_text=_("Current VPN access status (ENABLED or DISABLED).")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("Timestamp when the VPN access record was first created.")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_("Timestamp when the VPN access status was last modified.")
    )

    class Meta:
        ordering = ['-updated_at']
        verbose_name = _('VPN Access')
        verbose_name_plural = _('VPN Access Records')
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at']),
        ]

    def __str__(self):
        return f"VPN Access: {self.employee.email} [{self.status}]"

    def enable(self):
        """
        Explicitly enables VPN access for the employee.
        Returns True if the status changed, False if already ENABLED.
        """
        if self.status != VPNAccessStatus.ENABLED:
            self.status = VPNAccessStatus.ENABLED
            self.save(update_fields=['status', 'updated_at'])
            return True
        return False

    def disable(self):
        """
        Explicitly disables VPN access for the employee.
        Returns True if the status changed, False if already DISABLED.
        """
        if self.status != VPNAccessStatus.DISABLED:
            self.status = VPNAccessStatus.DISABLED
            self.save(update_fields=['status', 'updated_at'])
            return True
        return False


class GitHubAccessStatus(models.TextChoices):
    """
    Status of an employee's organization membership in GitHub.
    """
    MEMBER = 'MEMBER', _('Member')
    REVOKED = 'REVOKED', _('Revoked')
    NOT_MEMBER = 'NOT_MEMBER', _('Not Member')


class GitHubMembership(models.Model):
    """
    Represents GitHub organization access state for an employee.
    Maintains local state representation and GitHub username mapping.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_("Unique identifier for GitHub membership record (UUIDv4).")
    )
    employee = models.OneToOneField(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='github_membership',
        help_text=_("Associated employee in HR system.")
    )
    github_username = models.CharField(
        max_length=100,
        db_index=True,
        help_text=_("Mapped GitHub username for the employee.")
    )
    org_name = models.CharField(
        max_length=100,
        default='reconcileos-org',
        help_text=_("GitHub organization name.")
    )
    status = models.CharField(
        max_length=20,
        choices=GitHubAccessStatus.choices,
        default=GitHubAccessStatus.MEMBER,
        db_index=True,
        help_text=_("Current GitHub organization access status (MEMBER, REVOKED, NOT_MEMBER).")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("Timestamp when GitHub membership record was created.")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_("Timestamp when GitHub membership status was last updated.")
    )

    class Meta:
        ordering = ['-updated_at']
        verbose_name = _('GitHub Membership')
        verbose_name_plural = _('GitHub Memberships')
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['github_username']),
        ]

    def __str__(self):
        return f"GitHub Membership: {self.github_username} [{self.status}] ({self.org_name})"

    def revoke(self):
        """
        Revokes organization access for the employee.
        Returns True if status changed, False if already REVOKED or NOT_MEMBER.
        """
        if self.status != GitHubAccessStatus.REVOKED:
            self.status = GitHubAccessStatus.REVOKED
            self.save(update_fields=['status', 'updated_at'])
            return True
        return False


class CloudRole(models.TextChoices):
    """
    Cloud IAM Roles assigned to an employee identity.
    """
    DEVELOPER_ROLE = 'DEVELOPER_ROLE', _('Developer Role')
    ADMIN_ROLE = 'ADMIN_ROLE', _('Admin Role')
    NO_ROLE = 'NO_ROLE', _('No Role')
    REVOKED = 'REVOKED', _('Revoked')


class CloudIAMAccess(models.Model):
    """
    Represents Cloud IAM role permissions state for an employee.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_("Unique identifier for Cloud IAM access record (UUIDv4).")
    )
    employee = models.OneToOneField(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='cloud_access',
        help_text=_("Associated employee in HR system.")
    )
    cloud_identity = models.CharField(
        max_length=100,
        db_index=True,
        help_text=_("Cloud identity ARN or User Principal Name.")
    )
    role = models.CharField(
        max_length=30,
        choices=CloudRole.choices,
        default=CloudRole.NO_ROLE,
        db_index=True,
        help_text=_("Current assigned Cloud IAM Role.")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("Timestamp when Cloud IAM access record was created.")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_("Timestamp when Cloud IAM access was last updated.")
    )

    class Meta:
        ordering = ['-updated_at']
        verbose_name = _('Cloud IAM Access')
        verbose_name_plural = _('Cloud IAM Access Records')
        indexes = [
            models.Index(fields=['role']),
        ]

    def __str__(self):
        return f"Cloud Access: {self.employee.email} [{self.role}]"

    def revoke(self):
        """
        Revokes all Cloud IAM role permissions for the employee.
        Returns True if role changed, False if already NO_ROLE or REVOKED.
        """
        if self.role not in [CloudRole.NO_ROLE, CloudRole.REVOKED]:
            self.role = CloudRole.NO_ROLE
            self.save(update_fields=['role', 'updated_at'])
            return True
        return False


class SlackAccountStatus(models.TextChoices):
    """
    Status of an employee's enterprise Slack account.
    """
    ACTIVE = 'ACTIVE', _('Active')
    DEACTIVATED = 'DEACTIVATED', _('Deactivated')
    DISABLED = 'DISABLED', _('Disabled')


class SlackAccount(models.Model):
    """
    Represents Slack workspace account state for an employee.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_("Unique identifier for Slack account record (UUIDv4).")
    )
    employee = models.OneToOneField(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='slack_account',
        help_text=_("Associated employee in HR system.")
    )
    slack_user_id = models.CharField(
        max_length=50,
        db_index=True,
        help_text=_("Slack User Member ID (e.g. U12345678).")
    )
    status = models.CharField(
        max_length=20,
        choices=SlackAccountStatus.choices,
        default=SlackAccountStatus.DEACTIVATED,
        db_index=True,
        help_text=_("Current Slack account status (ACTIVE or DEACTIVATED).")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("Timestamp when Slack account record was created.")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_("Timestamp when Slack account status was last updated.")
    )

    class Meta:
        ordering = ['-updated_at']
        verbose_name = _('Slack Account')
        verbose_name_plural = _('Slack Accounts')
        indexes = [
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Slack Account: {self.employee.email} [{self.status}]"

    def deactivate(self):
        """
        Deactivates the employee's Slack workspace account.
        Returns True if status changed, False if already DEACTIVATED or DISABLED.
        """
        if self.status == SlackAccountStatus.ACTIVE:
            self.status = SlackAccountStatus.DEACTIVATED
            self.save(update_fields=['status', 'updated_at'])
            return True
        return False
