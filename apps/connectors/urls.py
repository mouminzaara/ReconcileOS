"""
URL routing for Simulated VPN Connector API endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VPNAccessViewSet

router = DefaultRouter()
router.register(r'', VPNAccessViewSet, basename='vpn-access')

urlpatterns = [
    path('', include(router.urls)),
]
