"""
URL Configuration for ReconcileOS Repair Planning Engine.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RepairPlanViewSet

app_name = 'workflows'

router = DefaultRouter()
router.register(r'plans', RepairPlanViewSet, basename='repair-plan')

urlpatterns = [
    path('', include(router.urls)),
]
