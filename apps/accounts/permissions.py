"""
Role-Based Access Control (RBAC) Permission Classes for ReconcileOS Django REST Framework.
"""

from rest_framework.permissions import BasePermission
from .models import UserRole, UserProfile


def _get_user_role(user) -> str:
    """Helper to safely retrieve the user's RBAC role string."""
    if not user or not user.is_authenticated:
        return None
    if user.is_superuser:
        return UserRole.ADMIN
    if hasattr(user, 'profile') and user.profile:
        return user.profile.role
    return UserRole.VIEWER


class IsAdminUserRole(BasePermission):
    """
    Allows access only to users with the ADMIN role (or Django superusers).
    ADMINs can manage employees, rules, approve repairs, execute repairs, and view audit logs.
    """

    def has_permission(self, request, view):
        role = _get_user_role(request.user)
        return role == UserRole.ADMIN


class IsOperatorUserRole(BasePermission):
    """
    Allows access to users with ADMIN or OPERATOR role.
    OPERATORs can view systems, run reconciliation audits, view drift violations, and generate repair plans.
    """

    def has_permission(self, request, view):
        role = _get_user_role(request.user)
        return role in [UserRole.ADMIN, UserRole.OPERATOR]


class IsViewerUserRole(BasePermission):
    """
    Allows access to any authenticated user (ADMIN, OPERATOR, or VIEWER).
    VIEWERs have read-only access.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)
