"""
URL routing for ReconcileOS Reconciliation Engine REST API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CollectedStateListView,
    CollectedStateDetailView,
    IntegrityViolationViewSet,
    RunReconciliationView,
    ContinuousMonitorView
)

router = DefaultRouter()
router.register(r'violations', IntegrityViolationViewSet, basename='integrityviolation')

urlpatterns = [
    path('state/', CollectedStateListView.as_view(), name='reconciliation-state-list'),
    path('state/<str:employee_id>/', CollectedStateDetailView.as_view(), name='reconciliation-state-detail'),
    path('run/', RunReconciliationView.as_view(), name='reconciliation-run'),
    path('monitor/', ContinuousMonitorView.as_view(), name='reconciliation-monitor'),
    path('', include(router.urls)),
]
