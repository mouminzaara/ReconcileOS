"""
Automated unit and integration test suite for Employees app.
"""

import uuid
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Employee, EmployeeStatus
from apps.accounts.models import UserProfile, UserRole


class EmployeeModelTests(TestCase):
    """Unit tests for the Employee model."""

    def test_create_employee_defaults(self):
        """Test creating an employee sets UUID, timestamps, and default ACTIVE status."""
        emp = Employee.objects.create(
            full_name="Alice Johnson",
            email="alice.johnson@example.com",
            department="Security & Infrastructure"
        )
        self.assertIsInstance(emp.id, uuid.UUID)
        self.assertEqual(emp.status, EmployeeStatus.ACTIVE)
        self.assertIsNotNone(emp.created_at)
        self.assertIsNotNone(emp.updated_at)
        self.assertIn("Alice Johnson", str(emp))
        self.assertIn("alice.johnson@example.com", str(emp))

    def test_terminate_method(self):
        """Test the terminate() helper method on the model."""
        emp = Employee.objects.create(
            full_name="Bob Smith",
            email="bob.smith@example.com",
            department="Engineering",
            status=EmployeeStatus.ACTIVE
        )
        status_changed = emp.terminate()
        self.assertTrue(status_changed)
        emp.refresh_from_db()
        self.assertEqual(emp.status, EmployeeStatus.TERMINATED)

        second_attempt = emp.terminate()
        self.assertFalse(second_attempt)
        emp.refresh_from_db()
        self.assertEqual(emp.status, EmployeeStatus.TERMINATED)


class EmployeeAPITests(APITestCase):
    """Integration tests for Employee REST API endpoints."""

    def setUp(self):
        self.admin_user = User.objects.create_superuser('admin_emp', 'admin@emp.com', 'admin123')
        UserProfile.objects.create(user=self.admin_user, role=UserRole.ADMIN)
        self.client.force_authenticate(user=self.admin_user)

        self.emp1 = Employee.objects.create(
            full_name="Carol Danvers",
            email="carol@example.com",
            department="Engineering",
            status=EmployeeStatus.ACTIVE
        )
        self.emp2 = Employee.objects.create(
            full_name="David Banner",
            email="david@example.com",
            department="DevOps",
            status=EmployeeStatus.TERMINATED
        )
        self.list_url = reverse('employee-list')

    def test_list_employees(self):
        """Test GET /api/v1/employees/ returns employee list."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(response.data['count'], 2)

    def test_filter_employees_by_status(self):
        """Test filtering employees by status=ACTIVE and status=TERMINATED."""
        response = self.client.get(f"{self.list_url}?status=ACTIVE")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['email'], 'carol@example.com')

        response = self.client.get(f"{self.list_url}?status=TERMINATED")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['email'], 'david@example.com')

    def test_search_employees(self):
        """Test searching employees by text query."""
        response = self.client.get(f"{self.list_url}?search=Carol")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['full_name'], 'Carol Danvers')

    def test_retrieve_employee_success(self):
        """Test GET /api/v1/employees/{id}/ retrieves employee details."""
        detail_url = reverse('employee-detail', kwargs={'pk': self.emp1.id})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.emp1.id))
        self.assertEqual(response.data['full_name'], "Carol Danvers")
        self.assertEqual(response.data['email'], "carol@example.com")
        self.assertEqual(response.data['status'], EmployeeStatus.ACTIVE)

    def test_retrieve_employee_not_found(self):
        """Test GET /api/v1/employees/{non_existent_uuid}/ returns 404."""
        random_uuid = uuid.uuid4()
        detail_url = reverse('employee-detail', kwargs={'pk': random_uuid})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_employee_success(self):
        """Test POST /api/v1/employees/ creates a new employee."""
        payload = {
            "full_name": "Elena Romanova",
            "email": "elena.romanova@example.com",
            "department": "Security",
            "status": "ACTIVE"
        }
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['full_name'], "Elena Romanova")
        self.assertEqual(response.data['email'], "elena.romanova@example.com")
        self.assertEqual(response.data['department'], "Security")
        self.assertEqual(response.data['status'], EmployeeStatus.ACTIVE)
        self.assertTrue(Employee.objects.filter(email="elena.romanova@example.com").exists())

    def test_create_employee_duplicate_email(self):
        """Test creating an employee with existing email fails with 400 validation error."""
        payload = {
            "full_name": "Carol Imposter",
            "email": "carol@example.com",
            "department": "HR"
        }
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_update_employee(self):
        """Test PUT / PATCH updates employee attributes."""
        detail_url = reverse('employee-detail', kwargs={'pk': self.emp1.id})
        patch_payload = {
            "department": "Executive Staff"
        }
        response = self.client.patch(detail_url, patch_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.emp1.refresh_from_db()
        self.assertEqual(self.emp1.department, "Executive Staff")

    def test_terminate_employee_endpoint(self):
        """Test POST /api/v1/employees/{id}/terminate/ explicitly terminates employee."""
        terminate_url = reverse('employee-terminate', kwargs={'pk': self.emp1.id})
        payload = {
            "reason": "Contract finished and offboarding initiated."
        }
        response = self.client.post(terminate_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertTrue(response.data['status_changed'])
        self.assertEqual(response.data['employee']['status'], EmployeeStatus.TERMINATED)
        self.assertEqual(response.data['reason'], "Contract finished and offboarding initiated.")

        self.emp1.refresh_from_db()
        self.assertEqual(self.emp1.status, EmployeeStatus.TERMINATED)

    def test_terminate_already_terminated_employee(self):
        """Test terminating an already terminated employee returns 200 with status_changed=False."""
        terminate_url = reverse('employee-terminate', kwargs={'pk': self.emp2.id})
        response = self.client.post(terminate_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertFalse(response.data['status_changed'])
        self.assertEqual(response.data['employee']['status'], EmployeeStatus.TERMINATED)

    def test_delete_employee(self):
        """Test DELETE /api/v1/employees/{id}/ removes employee."""
        detail_url = reverse('employee-detail', kwargs={'pk': self.emp1.id})
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Employee.objects.filter(pk=self.emp1.id).exists())
