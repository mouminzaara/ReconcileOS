"""
URL Configuration for ReconcileOS Human-in-the-Loop Approvals Engine.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ApprovalRequestViewSet

app_name = 'approvals'

router = DefaultRouter()
router.register(r'', ApprovalRequestViewSet, basename='approval-request')

urlpatterns = [
    path('', include(router.urls)),
]
