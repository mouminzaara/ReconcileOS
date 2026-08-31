"""
ReconcileOS Root URL Configuration.

The `urlpatterns` list routes URLs to views.
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint to verify ReconcileOS API service status.
    """
    return Response({
        "status": "healthy",
        "service": "ReconcileOS API Core",
        "version": "0.1.0",
        "timestamp": timezone.now().isoformat(),
        "active_modules": [
            "accounts",
            "employees",
            "connectors",
            "rules",
            "reconciliation",
            "workflows",
            "approvals",
            "audit",
        ]
    })


urlpatterns = [
    # Django Admin Site
    path('admin/', admin.site.urls),

    # Health Check API
    path('api/v1/health/', health_check, name='api_health_check'),

    # Modular API Routers
    path('api/v1/employees/', include('apps.employees.urls')),
    path('api/v1/vpn/', include('apps.connectors.urls')),
    path('api/v1/rules/', include('apps.rules.urls')),
    path('api/v1/reconciliation/', include('apps.reconciliation.urls')),
    path('api/v1/workflows/', include('apps.workflows.urls')),
    path('api/v1/approvals/', include('apps.approvals.urls')),
    path('api/v1/audit/', include('apps.audit.urls')),
    path('api/v1/auth/', include('apps.accounts.urls')),
]
