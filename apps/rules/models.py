"""
Models for the ReconcileOS Invariant Rule Engine.
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class RuleSeverity(models.TextChoices):
    """
    Severity / Risk level associated with a rule violation.
    """
    CRITICAL = 'CRITICAL', _('Critical')
    HIGH = 'HIGH', _('High')
    MEDIUM = 'MEDIUM', _('Medium')
    LOW = 'LOW', _('Low')


class Rule(models.Model):
    """
    Represents a declarative multi-system invariant security rule.
    
    A rule specifies expected target system state given a source system condition.
    Example:
      source_system: "HR"
      condition_attribute: "status"
      condition_value: "TERMINATED"
      target_system: "VPN"
      expected_attribute: "status"
      expected_value: "DISABLED"
    
    Expresses: "If employee status in HR is TERMINATED, VPN access status must be DISABLED."
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_("Unique identifier for the rule (UUIDv4).")
    )
    rule_code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text=_("Unique human-readable identifier code (e.g. INV-RULE-001).")
    )
    name = models.CharField(
        max_length=255,
        help_text=_("Short descriptive title of the invariant rule.")
    )
    description = models.TextField(
        blank=True,
        help_text=_("Detailed rationale and compliance justification for this invariant rule.")
    )
    
    # Source condition mapping
    source_system = models.CharField(
        max_length=50,
        default='HR',
        db_index=True,
        help_text=_("Source system of record (e.g. HR).")
    )
    condition_attribute = models.CharField(
        max_length=50,
        default='status',
        help_text=_("Attribute name in source system to evaluate (e.g. status).")
    )
    condition_value = models.CharField(
        max_length=50,
        default='TERMINATED',
        help_text=_("Attribute value in source system that triggers this rule (e.g. TERMINATED).")
    )
    
    # Target invariant expectation mapping
    target_system = models.CharField(
        max_length=50,
        default='VPN',
        db_index=True,
        help_text=_("Downstream target system (e.g. VPN, GitHub, Cloud).")
    )
    expected_attribute = models.CharField(
        max_length=50,
        default='status',
        help_text=_("Required attribute name in target system (e.g. status, access_status).")
    )
    expected_value = models.CharField(
        max_length=50,
        default='DISABLED',
        help_text=_("Required attribute value in target system (e.g. DISABLED).")
    )

    severity = models.CharField(
        max_length=20,
        choices=RuleSeverity.choices,
        default=RuleSeverity.CRITICAL,
        db_index=True,
        help_text=_("Severity level assigned when this invariant is violated.")
    )
    is_enabled = models.BooleanField(
        default=True,
        db_index=True,
        help_text=_("Whether this rule is active and evaluated during integrity audits.")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("Timestamp when the rule was created.")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_("Timestamp when the rule definition was last modified.")
    )

    class Meta:
        ordering = ['rule_code']
        verbose_name = _('Invariant Rule')
        verbose_name_plural = _('Invariant Rules')
        indexes = [
            models.Index(fields=['rule_code']),
            models.Index(fields=['source_system', 'target_system']),
            models.Index(fields=['is_enabled', 'severity']),
        ]

    def __str__(self):
        return f"{self.rule_code}: {self.name} [{self.source_system} -> {self.target_system}]"

    def matches_condition(self, source_val):
        """
        Helper method to check if a source system value triggers this rule condition.
        Case-insensitive string comparison.
        """
        if not source_val:
            return False
        return str(source_val).strip().upper() == str(self.condition_value).strip().upper()

    def evaluates_drift(self, source_val, target_val):
        """
        Helper method to check if an authorization drift exists.
        Returns True if source_val triggers rule condition AND target_val does NOT match expected_value.
        """
        if not self.is_enabled:
            return False
        
        condition_met = self.matches_condition(source_val)
        if not condition_met:
            return False
        
        target_matches_expected = str(target_val or '').strip().upper() == str(self.expected_value).strip().upper()
        return not target_matches_expected
