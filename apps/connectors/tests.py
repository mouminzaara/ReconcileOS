"""
Automated unit and integration test suite for Simulated VPN Connector app.
"""

import uuid
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from apps.employees.models import Employee, EmployeeStatus
from apps.accounts.models import UserProfile, UserRole
from .models import VPNAccess, VPNAccessStatus


class VPNAccessModelTests(TestCase):
    """Unit tests for the VPNAccess model and database constraints."""

    def setUp(self):
        self.employee = Employee.objects.create(
            full_name="Alice Security",
            email="alice.sec@company.com",
            department="Cybersecurity",
            status=EmployeeStatus.ACTIVE
        )

    def test_create_vpn_access_defaults(self):
        """Test creating VPNAccess sets default DISABLED status, timestamps, and UUID."""
        vpn = VPNAccess.objects.create(employee=self.employee)
        self.assertIsInstance(vpn.id, uuid.UUID)
        self.assertEqual(vpn.status, VPNAccessStatus.DISABLED)
        self.assertIsNotNone(vpn.created_at)
        self.assertIsNotNone(vpn.updated_at)
        self.assertEqual(vpn.employee, self.employee)
        self.assertIn("alice.sec@company.com", str(vpn))
        self.assertIn("DISABLED", str(vpn))

    def test_enable_and_disable_methods(self):
        """Test the enable() and disable() helper methods on the VPNAccess model."""
        vpn = VPNAccess.objects.create(employee=self.employee, status=VPNAccessStatus.DISABLED)

        changed = vpn.enable()
        self.assertTrue(changed)
        vpn.refresh_from_db()
        self.assertEqual(vpn.status, VPNAccessStatus.ENABLED)

        changed_again = vpn.enable()
        self.assertFalse(changed_again)

        changed = vpn.disable()
        self.assertTrue(changed)
        vpn.refresh_from_db()
        self.assertEqual(vpn.status, VPNAccessStatus.DISABLED)

        changed_again = vpn.disable()
        self.assertFalse(changed_again)

    def test_prevent_duplicate_vpn_access_db_constraint(self):
        """
        Test that creating more than one VPNAccess record for the same employee
        raises a database-level IntegrityError due to OneToOneField constraint.
        """
        VPNAccess.objects.create(employee=self.employee, status=VPNAccessStatus.ENABLED)
        
        with self.assertRaises(IntegrityError):
            VPNAccess.objects.create(employee=self.employee, status=VPNAccessStatus.DISABLED)


class VPNAccessAPITests(APITestCase):
    """Integration tests for the Simulated VPN Connector REST API endpoints."""

    def setUp(self):
        self.admin_user = User.objects.create_superuser('admin_vpn', 'admin@vpn.com', 'admin123')
        UserProfile.objects.create(user=self.admin_user, role=UserRole.ADMIN)
        self.client.force_authenticate(user=self.admin_user)

        self.active_emp = Employee.objects.create(
            full_name="Bob Developer",
            email="bob.dev@company.com",
            department="Engineering",
            status=EmployeeStatus.ACTIVE
        )
        self.term_emp = Employee.objects.create(
            full_name="Charlie Contractor",
            email="charlie.term@company.com",
            department="Sales",
            status=EmployeeStatus.TERMINATED
        )
        self.unprovisioned_emp = Employee.objects.create(
            full_name="Diana Newhire",
            email="diana.new@company.com",
            department="Platform",
            status=EmployeeStatus.ACTIVE
        )

        self.vpn_bob = VPNAccess.objects.create(
            employee=self.active_emp,
            status=VPNAccessStatus.ENABLED
        )
        self.vpn_charlie = VPNAccess.objects.create(
            employee=self.term_emp,
            status=VPNAccessStatus.DISABLED
        )

        self.list_url = reverse('vpn-access-list')

    def test_list_vpn_access_records(self):
        """Test GET /api/v1/vpn/ returns all VPN access records."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(response.data['count'], 2)

    def test_filter_vpn_access_by_status(self):
        """Test filtering VPN access records by status."""
        response = self.client.get(f"{self.list_url}?status=ENABLED")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['employee_email'], 'bob.dev@company.com')

        response = self.client.get(f"{self.list_url}?status=DISABLED")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['employee_email'], 'charlie.term@company.com')

    def test_search_vpn_access(self):
        """Test searching VPN access records by employee name/email."""
        response = self.client.get(f"{self.list_url}?search=Bob")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['employee_name'], 'Bob Developer')

    def test_retrieve_existing_vpn_access(self):
        """Test GET /api/v1/vpn/<employee_id>/ for an employee with existing record."""
        detail_url = reverse('vpn-access-detail', kwargs={'employee_id': self.active_emp.id})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['employee_id'], str(self.active_emp.id))
        self.assertEqual(response.data['employee_email'], 'bob.dev@company.com')
        self.assertEqual(response.data['status'], VPNAccessStatus.ENABLED)
        self.assertEqual(response.data['status_display'], 'Enabled')

    def test_retrieve_auto_initializes_vpn_access_for_unprovisioned_employee(self):
        """
        Test GET /api/v1/vpn/<employee_id>/ auto-initializes a DISABLED VPN access record
        when the employee exists in HR but has no prior VPN record.
        """
        self.assertFalse(VPNAccess.objects.filter(employee=self.unprovisioned_emp).exists())

        detail_url = reverse('vpn-access-detail', kwargs={'employee_id': self.unprovisioned_emp.id})
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['employee_id'], str(self.unprovisioned_emp.id))
        self.assertEqual(response.data['employee_email'], 'diana.new@company.com')
        self.assertEqual(response.data['status'], VPNAccessStatus.DISABLED)
        self.assertEqual(response.data['status_display'], 'Disabled')

        self.assertTrue(VPNAccess.objects.filter(employee=self.unprovisioned_emp).exists())
        vpn_rec = VPNAccess.objects.get(employee=self.unprovisioned_emp)
        self.assertEqual(vpn_rec.status, VPNAccessStatus.DISABLED)

    def test_retrieve_invalid_employee_id_returns_404(self):
        """Test GET /api/v1/vpn/<employee_id>/ returns 404 for non-existent and malformed UUIDs."""
        random_uuid = uuid.uuid4()
        detail_url = reverse('vpn-access-detail', kwargs={'employee_id': random_uuid})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        bad_url = reverse('vpn-access-detail', kwargs={'employee_id': 'invalid-uuid-123'})
        response = self.client.get(bad_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_enable_vpn_access_existing_record(self):
        """Test POST /api/v1/vpn/<employee_id>/enable/ enables VPN access."""
        enable_url = reverse('vpn-access-enable', kwargs={'employee_id': self.term_emp.id})
        response = self.client.post(enable_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertTrue(response.data['status_changed'])
        self.assertEqual(response.data['action'], 'ENABLE')
        self.assertEqual(response.data['vpn_access']['status'], VPNAccessStatus.ENABLED)

        self.vpn_charlie.refresh_from_db()
        self.assertEqual(self.vpn_charlie.status, VPNAccessStatus.ENABLED)

    def test_enable_vpn_access_already_enabled(self):
        """Test enabling already ENABLED VPN returns 200 with status_changed=False."""
        enable_url = reverse('vpn-access-enable', kwargs={'employee_id': self.active_emp.id})
        response = self.client.post(enable_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertFalse(response.data['status_changed'])
        self.assertEqual(response.data['vpn_access']['status'], VPNAccessStatus.ENABLED)

    def test_enable_vpn_access_auto_initializes_and_enables(self):
        """Test enabling VPN for an unprovisioned employee auto-creates and enables it."""
        self.assertFalse(VPNAccess.objects.filter(employee=self.unprovisioned_emp).exists())

        enable_url = reverse('vpn-access-enable', kwargs={'employee_id': self.unprovisioned_emp.id})
        response = self.client.post(enable_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertTrue(response.data['status_changed'])
        self.assertEqual(response.data['vpn_access']['status'], VPNAccessStatus.ENABLED)

        vpn_rec = VPNAccess.objects.get(employee=self.unprovisioned_emp)
        self.assertEqual(vpn_rec.status, VPNAccessStatus.ENABLED)

    def test_disable_vpn_access_existing_record(self):
        """Test POST /api/v1/vpn/<employee_id>/disable/ disables VPN access."""
        disable_url = reverse('vpn-access-disable', kwargs={'employee_id': self.active_emp.id})
        response = self.client.post(disable_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertTrue(response.data['status_changed'])
        self.assertEqual(response.data['action'], 'DISABLE')
        self.assertEqual(response.data['vpn_access']['status'], VPNAccessStatus.DISABLED)

        self.vpn_bob.refresh_from_db()
        self.assertEqual(self.vpn_bob.status, VPNAccessStatus.DISABLED)

    def test_disable_vpn_access_already_disabled(self):
        """Test disabling already DISABLED VPN returns 200 with status_changed=False."""
        disable_url = reverse('vpn-access-disable', kwargs={'employee_id': self.term_emp.id})
        response = self.client.post(disable_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertFalse(response.data['status_changed'])
        self.assertEqual(response.data['vpn_access']['status'], VPNAccessStatus.DISABLED)

    def test_enable_disable_invalid_employee_returns_404(self):
        """Test enable and disable endpoints return 404 for invalid employee IDs."""
        random_uuid = uuid.uuid4()
        enable_url = reverse('vpn-access-enable', kwargs={'employee_id': random_uuid})
        response = self.client.post(enable_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        disable_url = reverse('vpn-access-disable', kwargs={'employee_id': random_uuid})
        response = self.client.post(disable_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class SeedDemoDriftCommandTests(TestCase):
    """Unit tests for the seed_demo_drift Django management command."""

    def test_seed_demo_drift_creates_rahul_kumar_drift_state(self):
        """Test executing seed_demo_drift creates Rahul Kumar with HR=TERMINATED and VPN=ENABLED."""
        from django.core.management import call_command

        call_command('seed_demo_drift')

        rahul = Employee.objects.get(email="rahul.kumar@reconcileos.internal")
        self.assertEqual(rahul.full_name, "Rahul Kumar")
        self.assertEqual(rahul.department, "DevOps & Cloud Integrity")
        self.assertEqual(rahul.status, EmployeeStatus.TERMINATED)

        vpn = VPNAccess.objects.get(employee=rahul)
        self.assertEqual(vpn.status, VPNAccessStatus.ENABLED)

    def test_seed_demo_drift_is_idempotent(self):
        """Test running seed_demo_drift multiple times maintains exact state without duplicates."""
        from django.core.management import call_command

        call_command('seed_demo_drift')
        call_command('seed_demo_drift')

        self.assertEqual(
            Employee.objects.filter(email="rahul.kumar@reconcileos.internal").count(),
            1
        )
        rahul = Employee.objects.get(email="rahul.kumar@reconcileos.internal")
        self.assertEqual(
            VPNAccess.objects.filter(employee=rahul).count(),
            1
        )
        self.assertEqual(rahul.status, EmployeeStatus.TERMINATED)
        self.assertEqual(rahul.vpn_access.status, VPNAccessStatus.ENABLED)
