"""
Automated backend tests for truthful Connected Systems health checks.
Verifies success, timeout, failure responses, and non-mutating behavior.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import UserProfile, UserRole
from apps.employees.models import Employee, EmployeeStatus
from apps.connectors.models import VPNAccess, VPNAccessStatus
from apps.connectors.adapters import ConnectorRegistry


class ConnectorHealthCheckAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.viewer_user = User.objects.create_user(username='viewer_health', password='password123')
        UserProfile.objects.create(user=self.viewer_user, role=UserRole.VIEWER)
        self.client.force_authenticate(user=self.viewer_user)

        self.employee = Employee.objects.create(
            full_name="Health Check Test Subject",
            email="health.test@example.com",
            department="QA & Automation",
            status=EmployeeStatus.ACTIVE
        )
        self.vpn_record = VPNAccess.objects.create(
            employee=self.employee,
            status=VPNAccessStatus.DISABLED
        )

    def test_all_connectors_health_check_success(self):
        """GET /api/v1/connectors/health/ returns status for all 5 systems truthfully."""
        response = self.client.get('/api/v1/connectors/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn('systems', response.data)

        systems = response.data['systems']
        self.assertIn('hr', systems)
        self.assertIn('vpn', systems)
        self.assertIn('github', systems)
        self.assertIn('cloud', systems)
        self.assertIn('slack', systems)

        # HR is real database of record
        self.assertEqual(systems['hr']['status'], 'HEALTHY')
        self.assertFalse(systems['hr']['is_simulated'])
        self.assertGreaterEqual(systems['hr']['latency_ms'], 0)

        # VPN is local simulation
        self.assertEqual(systems['vpn']['status'], 'SIMULATED_HEALTHY')
        self.assertTrue(systems['vpn']['is_simulated'])
        self.assertFalse(systems['vpn']['is_live_external'])

        # GitHub is database fallback (no live token in test)
        self.assertEqual(systems['github']['status'], 'DATABASE_FALLBACK_HEALTHY')
        self.assertTrue(systems['github']['is_simulated'])

    def test_single_connector_health_check_vpn(self):
        """GET /api/v1/connectors/vpn/health/ returns VPN simulation telemetry."""
        response = self.client.get('/api/v1/connectors/vpn/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['key'], 'vpn')
        self.assertEqual(response.data['status'], 'SIMULATED_HEALTHY')
        self.assertTrue(response.data['is_simulated'])
        self.assertFalse(response.data['is_live_external'])
        self.assertIn('functional', response.data['message'].lower())

    def test_connector_health_check_timeout_response(self):
        """Health check returns 504 and TIMEOUT status when simulated timeout occurs."""
        response = self.client.get('/api/v1/connectors/vpn/health/?simulate_timeout=1')
        self.assertEqual(response.status_code, status.HTTP_504_GATEWAY_TIMEOUT)
        self.assertEqual(response.data['status'], 'TIMEOUT')
        self.assertIn('timed out', response.data['message'].lower())
        self.assertGreaterEqual(response.data['latency_ms'], 1000)

    def test_connector_health_check_failure_response(self):
        """Health check returns 503 and ERROR status when error occurs."""
        response = self.client.get('/api/v1/connectors/vpn/health/?simulate_error=1')
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.data['status'], 'ERROR')
        self.assertIn('failure', response.data['message'].lower())

    def test_connector_adapter_failure_hook_detected(self):
        """When VPNConnectorAdapter has testing failure mode active, health check truthfully reflects failure."""
        adapter = ConnectorRegistry.get_connector('vpn')
        adapter.set_simulated_failure(fail_next_n=2)
        try:
            response = self.client.get('/api/v1/connectors/vpn/health/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['status'], 'SIMULATED_FAILURE')
            self.assertIn('hook is currently active', response.data['message'])
        finally:
            adapter.fail_next_n_attempts = 0

    def test_unsupported_connector_returns_404(self):
        """Unknown system key returns 404 with UNSUPPORTED status."""
        response = self.client.get('/api/v1/connectors/unknown_gateway/health/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['status'], 'UNSUPPORTED')

    def test_health_check_does_not_mutate_state(self):
        """Health check must never alter employee, VPN access, or system state."""
        vpn_before = VPNAccess.objects.get(pk=self.vpn_record.pk)
        self.assertEqual(vpn_before.status, VPNAccessStatus.DISABLED)

        # Run health checks multiple times
        self.client.get('/api/v1/connectors/health/')
        self.client.get('/api/v1/connectors/vpn/health/')
        self.client.post('/api/v1/connectors/vpn/ping/')

        vpn_after = VPNAccess.objects.get(pk=self.vpn_record.pk)
        self.assertEqual(vpn_after.status, VPNAccessStatus.DISABLED)
        self.assertEqual(vpn_after.updated_at, vpn_before.updated_at)
