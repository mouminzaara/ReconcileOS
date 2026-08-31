"""
Employee model for ReconcileOS HR system.
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class EmployeeStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', _('Active')
    TERMINATED = 'TERMINATED', _('Terminated')


class Employee(models.Model):
    """
    Represents an employee in the primary HR system of record.
    ReconcileOS monitors changes to employees (specifically status transitions like TERMINATED)
    to verify and enforce least-privilege compliance across downstream connected applications.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_("Unique identifier for the employee (UUIDv4).")
    )
    full_name = models.CharField(
        max_length=255,
        help_text=_("Full legal or professional name of the employee.")
    )
    email = models.EmailField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text=_("Corporate email address (unique identifier across systems).")
    )
    department = models.CharField(
        max_length=100,
        db_index=True,
        help_text=_("Department or organizational unit (e.g. Engineering, Sales, DevOps).")
    )
    status = models.CharField(
        max_length=20,
        choices=EmployeeStatus.choices,
        default=EmployeeStatus.ACTIVE,
        db_index=True,
        help_text=_("Current employment status in the HR system.")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("Timestamp when the employee record was created.")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_("Timestamp when the employee record was last updated.")
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Employee')
        verbose_name_plural = _('Employees')
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['status']),
            models.Index(fields=['department']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.full_name} <{self.email}> [{self.status}]"

    def terminate(self):
        """
        Explicitly marks the employee status as TERMINATED.
        Returns True if status changed, False if already terminated.
        """
        if self.status != EmployeeStatus.TERMINATED:
            self.status = EmployeeStatus.TERMINATED
            self.save(update_fields=['status', 'updated_at'])
            return True
        return False
