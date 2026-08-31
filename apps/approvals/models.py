"""
Models for ReconcileOS Human-in-the-Loop Approvals Engine.
"""

import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class ApprovalDecision(models.TextChoices):
    """
    Status of an approval decision for a repair plan.
    """
    PENDING = 'PENDING', _('Pending')
    APPROVED = 'APPROVED', _('Approved')
    REJECTED = 'REJECTED', _('Rejected')


class ApprovalRequest(models.Model):
    """
    Represents an explicit human-in-the-loop approval request for a sensitive repair plan.

    Before a repair plan can become eligible for execution, an administrator or authorized user
    must approve the request.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_("Unique identifier for the approval request (UUIDv4).")
    )
    repair_plan = models.ForeignKey(
        'workflows.RepairPlan',
        on_delete=models.CASCADE,
        related_name='approval_requests',
        help_text=_("Target repair plan requiring human approval.")
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approval_requests_sent',
        help_text=_("User or automated process that requested approval.")
    )
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approval_decisions_made',
        help_text=_("Administrator who made the approval/rejection decision.")
    )
    decision = models.CharField(
        max_length=20,
        choices=ApprovalDecision.choices,
        default=ApprovalDecision.PENDING,
        db_index=True,
        help_text=_("Current decision status of the approval request (PENDING, APPROVED, REJECTED).")
    )
    decided_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Timestamp when the decision was made.")
    )
    comment = models.TextField(
        blank=True,
        default='',
        help_text=_("Optional rationale or feedback provided by the approver.")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("Timestamp when the approval request was created.")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_("Timestamp when the approval request record was last modified.")
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Approval Request')
        verbose_name_plural = _('Approval Requests')
        indexes = [
            models.Index(fields=['decision']),
            models.Index(fields=['repair_plan', 'decision']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return (
            f"Approval Request [{self.decision}]: Plan ID {self.repair_plan_id} "
            f"({self.repair_plan.action} for {self.repair_plan.employee.full_name})"
        )

    @property
    def is_pending(self) -> bool:
        return self.decision == ApprovalDecision.PENDING

    @property
    def is_approved(self) -> bool:
        return self.decision == ApprovalDecision.APPROVED

    @property
    def is_rejected(self) -> bool:
        return self.decision == ApprovalDecision.REJECTED
