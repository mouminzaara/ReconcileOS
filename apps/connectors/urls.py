from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VPNAccessViewSet, ConnectorHealthCheckView

router = DefaultRouter()
router.register(r'', VPNAccessViewSet, basename='vpn-access')

urlpatterns = [
    path('health/', ConnectorHealthCheckView.as_view(), name='connectors-health'),
    path('<str:system_key>/health/', ConnectorHealthCheckView.as_view(), name='connector-system-health'),
    path('<str:system_key>/ping/', ConnectorHealthCheckView.as_view(), name='connector-system-ping'),
    path('', include(router.urls)),
]
