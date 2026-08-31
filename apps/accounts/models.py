"""
Accounts models for ReconcileOS.

Defines UserProfile and Role-Based Access Control (RBAC) choices (ADMIN, OPERATOR, VIEWER).
"""

import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class UserRole(models.TextChoices):
    """
    Role-Based Access Control (RBAC) choices for ReconcileOS.
    """
    ADMIN = 'ADMIN', _('Administrator')
    OPERATOR = 'OPERATOR', _('Security Operator')
    VIEWER = 'VIEWER', _('Auditor / Read-Only Viewer')


class UserProfile(models.Model):
    """
    Extends standard Django User with ReconcileOS RBAC role and profile metadata.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_("Unique identifier for user profile (UUIDv4).")
    )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        help_text=_("Associated Django user model instance.")
    )
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.VIEWER,
        db_index=True,
        help_text=_("Assigned RBAC role (ADMIN, OPERATOR, VIEWER).")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')
        indexes = [
            models.Index(fields=['role']),
        ]

    def __str__(self):
        return f"{self.user.username} Profile [{self.role}]"

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN or self.user.is_superuser

    @property
    def is_operator(self) -> bool:
        return self.role in [UserRole.ADMIN, UserRole.OPERATOR] or self.user.is_superuser

    @property
    def is_viewer(self) -> bool:
        return True  # All authenticated users have at least VIEWER permissions
