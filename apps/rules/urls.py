"""
URL routing for ReconcileOS Invariant Rule Engine REST API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RuleViewSet

router = DefaultRouter()
router.register(r'', RuleViewSet, basename='rule')

urlpatterns = [
    path('', include(router.urls)),
]
