"""
Comprehensive RBAC Permission Tests for VPNAccessViewSet (Phase 2C).

Tests role-based access control across all roles (Anonymous, VIEWER, OPERATOR, ADMIN)
for all standard and custom actions (list, retrieve, create, update, partial_update, destroy, enable, disable).
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.employees.models import Employee, EmployeeStatus
from apps.accounts.models import UserProfile, UserRole
from apps.connectors.models import VPNAccess, VPNAccessStatus


class VPNAccessRBACTestCase(TestCase):
    """
    Role-Based Access Control test suite for VPN endpoints.
    """

    def setUp(self):
        self.client = APIClient()

        # 1. Setup users with profiles
        self.admin_user = User.objects.create_user('admin_user', 'admin@example.com', 'password123')
        UserProfile.objects.create(user=self.admin_user, role=UserRole.ADMIN)

        self.operator_user = User.objects.create_user('operator_user', 'operator@example.com', 'password123')
        UserProfile.objects.create(user=self.operator_user, role=UserRole.OPERATOR)

        self.viewer_user = User.objects.create_user('viewer_user', 'viewer@example.com', 'password123')
        UserProfile.objects.create(user=self.viewer_user, role=UserRole.VIEWER)

        # 2. Setup employee and existing VPN record
        self.employee1 = Employee.objects.create(
            full_name="Alice Developer",
            email="alice@company.com",
            department="Engineering",
            status=EmployeeStatus.ACTIVE
        )
        self.vpn1 = VPNAccess.objects.create(
            employee=self.employee1,
            status=VPNAccessStatus.ENABLED
        )

        self.employee2 = Employee.objects.create(
            full_name="Bob Contractor",
            email="bob@company.com",
            department="Operations",
            status=EmployeeStatus.TERMINATED
        )

        self.list_url = reverse('vpn-access-list')
        self.detail_url = reverse('vpn-access-detail', kwargs={'employee_id': self.employee1.id})
        self.enable_url = reverse('vpn-access-enable', kwargs={'employee_id': self.employee1.id})
        self.disable_url = reverse('vpn-access-disable', kwargs={'employee_id': self.employee1.id})

    # ==========================
    # ANONYMOUS USERS (HTTP 401)
    # ==========================
    def test_anonymous_user_blocked_from_all_endpoints(self):
        """Anonymous users must be denied access to all VPN read and mutate endpoints."""
        self.client.logout()

        # Read actions
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        resp = self.client.get(self.detail_url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # Mutate actions
        resp = self.client.post(self.list_url, {'employee': str(self.employee2.id), 'status': 'DISABLED'})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        resp = self.client.post(self.enable_url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        resp = self.client.post(self.disable_url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        resp = self.client.delete(self.detail_url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    # ==========================
    # VIEWER ROLE (HTTP 200 Read, HTTP 403 Mutate)
    # ==========================
    def test_viewer_allowed_read_actions(self):
        """VIEWER users can list and retrieve VPN records."""
        self.client.force_authenticate(user=self.viewer_user)

        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        resp = self.client.get(self.detail_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['employee_email'], 'alice@company.com')

    def test_viewer_denied_all_mutations(self):
        """VIEWER users are strictly blocked (403) from all mutating actions."""
        self.client.force_authenticate(user=self.viewer_user)

        # 1. Custom action: enable
        resp = self.client.post(self.enable_url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # 2. Custom action: disable
        resp = self.client.post(self.disable_url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # 3. Create
        resp = self.client.post(self.list_url, {'employee': str(self.employee2.id), 'status': 'DISABLED'})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # 4. Update (PUT)
        resp = self.client.put(self.detail_url, {'employee': str(self.employee1.id), 'status': 'DISABLED'})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # 5. Partial Update (PATCH)
        resp = self.client.patch(self.detail_url, {'status': 'DISABLED'})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # 6. Destroy (DELETE)
        resp = self.client.delete(self.detail_url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    # ==========================
    # OPERATOR ROLE (HTTP 200 Read, HTTP 403 Mutate)
    # ==========================
    def test_operator_allowed_read_actions(self):
        """OPERATOR users can list and retrieve VPN records."""
        self.client.force_authenticate(user=self.operator_user)

        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        resp = self.client.get(self.detail_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_operator_denied_all_mutations(self):
        """OPERATOR users can view systems, but cannot mutate VPN access directly (403)."""
        self.client.force_authenticate(user=self.operator_user)

        # 1. Custom action: enable
        resp = self.client.post(self.enable_url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # 2. Custom action: disable
        resp = self.client.post(self.disable_url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # 3. Create
        resp = self.client.post(self.list_url, {'employee': str(self.employee2.id), 'status': 'DISABLED'})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # 4. Update (PUT)
        resp = self.client.put(self.detail_url, {'employee': str(self.employee1.id), 'status': 'DISABLED'})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # 5. Partial Update (PATCH)
        resp = self.client.patch(self.detail_url, {'status': 'DISABLED'})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # 6. Destroy (DELETE)
        resp = self.client.delete(self.detail_url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    # ==========================
    # ADMIN ROLE (HTTP 200 / 201 / 204 Allowed)
    # ==========================
    def test_admin_allowed_all_read_and_mutating_actions(self):
        """ADMIN users have full authorization to read and mutate VPN access records."""
        self.client.force_authenticate(user=self.admin_user)

        # Read
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # Custom action: disable
        resp = self.client.post(self.disable_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['action'], 'DISABLE')
        self.assertEqual(resp.data['vpn_access']['status'], 'DISABLED')

        # Custom action: enable
        resp = self.client.post(self.enable_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['action'], 'ENABLE')
        self.assertEqual(resp.data['vpn_access']['status'], 'ENABLED')

        # Partial update (PATCH)
        resp = self.client.patch(self.detail_url, {'status': 'DISABLED'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['status'], 'DISABLED')

        # Create explicit VPN access for employee2
        resp = self.client.post(self.list_url, {'employee': str(self.employee2.id), 'status': 'DISABLED'})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # Destroy (DELETE)
        emp2_detail = reverse('vpn-access-detail', kwargs={'employee_id': self.employee2.id})
        resp = self.client.delete(emp2_detail)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
