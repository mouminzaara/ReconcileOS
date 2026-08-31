"""
Database models for ReconcileOS Reconciliation Engine & Integrity Violations.
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.rules.models import RuleSeverity


class ViolationStatus(models.TextChoices):
    """
    Status lifecycle of an integrity violation.
    """
    OPEN = 'OPEN', _('Open')
    RESOLVED = 'RESOLVED', _('Resolved')


class IntegrityViolation(models.Model):
    """
    Represents an authorization drift / invariant rule violation detected by ReconcileOS.
    
    Stores the exact expected state vs actual state recorded at detection time.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_("Unique identifier for the integrity violation (UUIDv4).")
    )
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='violations',
        help_text=_("Employee associated with this authorization drift.")
    )
    rule = models.ForeignKey(
        'rules.Rule',
        on_delete=models.CASCADE,
        related_name='violations',
        help_text=_("Invariant rule that was violated.")
    )
    affected_system = models.CharField(
        max_length=50,
        db_index=True,
        help_text=_("Target system where authorization drift exists (e.g. VPN).")
    )
    expected_state = models.CharField(
        max_length=50,
        help_text=_("Expected value required by invariant rule (e.g. DISABLED).")
    )
    actual_state = models.CharField(
        max_length=50,
        help_text=_("Actual state detected in target system (e.g. ENABLED).")
    )
    severity = models.CharField(
        max_length=20,
        choices=RuleSeverity.choices,
        default=RuleSeverity.CRITICAL,
        db_index=True,
        help_text=_("Severity level assigned to this violation.")
    )
    status = models.CharField(
        max_length=20,
        choices=ViolationStatus.choices,
        default=ViolationStatus.OPEN,
        db_index=True,
        help_text=_("Current status of the violation (OPEN or RESOLVED).")
    )

    detected_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("Timestamp when the violation was first detected.")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_("Timestamp when the violation record was last updated.")
    )

    class Meta:
        ordering = ['-detected_at']
        verbose_name = _('Integrity Violation')
        verbose_name_plural = _('Integrity Violations')
        indexes = [
            models.Index(fields=['status', 'severity']),
            models.Index(fields=['employee', 'rule', 'status']),
            models.Index(fields=['affected_system', 'status']),
        ]

    def __str__(self):
        return (
            f"Violation [{self.status}]: {self.employee.full_name} - {self.rule.rule_code} "
            f"[{self.affected_system}: Expected {self.expected_state}, Actual {self.actual_state}]"
        )
