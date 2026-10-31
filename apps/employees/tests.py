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


from apps.audit.models import AuditLog, AuditEventType
from apps.audit.services import AuditLogger
from apps.connectors.models import VPNAccess, VPNAccessStatus
from apps.rules.models import Rule, RuleSeverity
from apps.reconciliation.models import IntegrityViolation, ViolationStatus
from apps.workflows.models import RepairPlan, PlanStatus
from apps.approvals.models import ApprovalRequest, ApprovalDecision


class EmployeeTerminationWorkflowTests(APITestCase):
    """
    Tests ensuring that employee termination records cryptographic audit events,
    triggers immediate drift reconciliation, detects downstream state mismatches,
    and safeguards the approval workflow without duplicate violations or plans.
    """

    def setUp(self):
        self.admin_user = User.objects.create_superuser('admin_workflow', 'admin@workflow.com', 'admin123')
        UserProfile.objects.create(user=self.admin_user, role=UserRole.ADMIN)
        self.client.force_authenticate(user=self.admin_user)

        self.employee = Employee.objects.create(
            full_name="Frank Castle",
            email="frank.castle@example.com",
            department="Security Operations",
            status=EmployeeStatus.ACTIVE
        )

        # Active VPN access
        self.vpn_access = VPNAccess.objects.create(
            employee=self.employee,
            status=VPNAccessStatus.ENABLED
        )

        # Invariant Rule: Terminated employees must have DISABLED VPN access
        self.rule = Rule.objects.create(
            rule_code="INV-VPN-001",
            name="Terminated Employee VPN Access",
            description="Terminated employees must not have active VPN access",
            source_system="HR",
            condition_attribute="status",
            condition_value="TERMINATED",
            target_system="VPN",
            expected_attribute="status",
            expected_value="DISABLED",
            severity=RuleSeverity.CRITICAL,
            is_enabled=True
        )

        self.terminate_url = reverse('employee-terminate', kwargs={'pk': self.employee.id})

    def test_termination_creates_audit_event_and_triggers_reconciliation(self):
        """
        Terminating an active employee:
        1. Emits EMPLOYEE_TERMINATED audit event with actor and state transitions.
        2. Evaluates rules and detects VPN drift (IntegrityViolation created).
        3. Generates RepairPlan in PENDING status requiring approval.
        4. Maintains valid cryptographic audit chain.
        """
        payload = {"reason": "Security offboarding protocol."}
        response = self.client.post(self.terminate_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertTrue(response.data['status_changed'])
        self.assertEqual(response.data['reconciliation']['status'], 'completed')
        self.assertEqual(response.data['reconciliation']['violations_detected_count'], 1)
        self.assertEqual(response.data['reconciliation']['repair_plans_generated_count'], 1)

        # 1. Verify audit log entry
        termination_log = AuditLog.objects.filter(
            employee=self.employee,
            event_type=AuditEventType.EMPLOYEE_TERMINATED
        ).first()

        self.assertIsNotNone(termination_log)
        self.assertEqual(termination_log.actor, 'admin_workflow')
        self.assertEqual(termination_log.system, 'HR')
        self.assertEqual(termination_log.previous_state, 'ACTIVE')
        self.assertEqual(termination_log.new_state, 'TERMINATED')
        self.assertEqual(termination_log.additional_metadata.get('reason'), 'Security offboarding protocol.')

        # 2. Verify drift violation created
        violation = IntegrityViolation.objects.filter(
            employee=self.employee,
            rule=self.rule,
            status=ViolationStatus.OPEN
        ).first()
        self.assertIsNotNone(violation)
        self.assertEqual(violation.actual_state, 'ENABLED')
        self.assertEqual(violation.expected_state, 'DISABLED')

        # 3. Verify repair plan created in PENDING status (not auto-executed)
        repair_plan = RepairPlan.objects.filter(
            employee=self.employee,
            violation=violation
        ).first()
        self.assertIsNotNone(repair_plan)
        self.assertEqual(repair_plan.status, PlanStatus.PENDING)

        # 4. Verify approval request created in PENDING status
        approval_req = ApprovalRequest.objects.filter(repair_plan=repair_plan).first()
        self.assertIsNotNone(approval_req)
        self.assertEqual(approval_req.decision, ApprovalDecision.PENDING)

        # 5. Verify cryptographic hash chain integrity
        is_valid, msg, details = AuditLogger.verify_chain_integrity()
        self.assertTrue(is_valid, f"Audit chain verification failed: {msg}")

    def test_repeated_termination_does_not_duplicate_lifecycle_events_or_plans(self):
        """
        Subsequent termination requests on an already terminated employee:
        1. Return status_changed=False.
        2. Do not emit duplicate EMPLOYEE_TERMINATED audit records.
        3. Do not create duplicate unresolved violations or duplicate repair plans.
        """
        # First termination
        res1 = self.client.post(self.terminate_url, {"reason": "Initial offboarding"}, format='json')
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        self.assertTrue(res1.data['status_changed'])

        audit_count_before = AuditLog.objects.filter(
            employee=self.employee,
            event_type=AuditEventType.EMPLOYEE_TERMINATED
        ).count()
        self.assertEqual(audit_count_before, 1)

        open_violation_count = IntegrityViolation.objects.filter(
            employee=self.employee,
            status=ViolationStatus.OPEN
        ).count()
        self.assertEqual(open_violation_count, 1)

        plan_count = RepairPlan.objects.filter(
            employee=self.employee,
            status=PlanStatus.PENDING
        ).count()
        self.assertEqual(plan_count, 1)

        # Second termination attempt
        res2 = self.client.post(self.terminate_url, {"reason": "Duplicate offboarding"}, format='json')
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertFalse(res2.data['status_changed'])
        self.assertEqual(res2.data['message'], "Employee is already terminated.")

        audit_count_after = AuditLog.objects.filter(
            employee=self.employee,
            event_type=AuditEventType.EMPLOYEE_TERMINATED
        ).count()
        self.assertEqual(audit_count_after, 1)

        self.assertEqual(
            IntegrityViolation.objects.filter(employee=self.employee, status=ViolationStatus.OPEN).count(),
            1
        )
        self.assertEqual(
            RepairPlan.objects.filter(employee=self.employee, status=PlanStatus.PENDING).count(),
            1
        )

        # Chain remains valid
        is_valid, _, _ = AuditLogger.verify_chain_integrity()
        self.assertTrue(is_valid)


from apps.connectors.models import GitHubMembership, GitHubAccessStatus, CloudIAMAccess, CloudRole, SlackAccount, SlackAccountStatus


class EmployeeConnectedSystemsTests(APITestCase):
    """
    Tests ensuring that employees accurately serialize their real connected systems
    and detailed connection states without hardcoded fallbacks or N+1 queries.
    """

    def setUp(self):
        self.admin_user = User.objects.create_superuser('admin_conn', 'admin@conn.com', 'admin123')
        UserProfile.objects.create(user=self.admin_user, role=UserRole.ADMIN)
        self.client.force_authenticate(user=self.admin_user)

    def test_employee_with_no_connected_systems(self):
        """Employee with no downstream accounts must only report HR."""
        emp = Employee.objects.create(
            full_name="No Systems User",
            email="nosystems@example.com",
            department="HR",
            status=EmployeeStatus.ACTIVE
        )

        detail_url = reverse('employee-detail', kwargs={'pk': emp.id})
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['systems_connected'], ['HR'])
        self.assertEqual(len(response.data['connected_systems']), 1)
        self.assertEqual(response.data['connected_systems'][0]['system'], 'HR')
        self.assertEqual(response.data['connected_systems'][0]['state'], 'CONNECTED')

    def test_employee_with_mixed_connected_and_disconnected_systems(self):
        """
        Employee with active VPN and GitHub, but revoked Cloud IAM and deactivated Slack:
        - systems_connected lists active systems only: HR, VPN, GitHub
        - connected_systems clearly distinguishes CONNECTED vs DISCONNECTED
        """
        emp = Employee.objects.create(
            full_name="Multi System User",
            email="multisystem@example.com",
            department="DevOps",
            status=EmployeeStatus.ACTIVE
        )
        VPNAccess.objects.create(employee=emp, status=VPNAccessStatus.ENABLED)
        GitHubMembership.objects.create(employee=emp, github_username="multi_gh", status=GitHubAccessStatus.MEMBER)
        CloudIAMAccess.objects.create(employee=emp, cloud_identity="arn:aws:iam::123:user/multi", role=CloudRole.REVOKED)
        SlackAccount.objects.create(employee=emp, slack_user_id="U99999999", status=SlackAccountStatus.DEACTIVATED)

        detail_url = reverse('employee-detail', kwargs={'pk': emp.id})
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('HR', response.data['systems_connected'])
        self.assertIn('VPN', response.data['systems_connected'])
        self.assertIn('GitHub', response.data['systems_connected'])
        self.assertNotIn('Cloud IAM', response.data['systems_connected'])
        self.assertNotIn('Slack', response.data['systems_connected'])

        details_by_key = {s['key']: s for s in response.data['connected_systems']}
        self.assertEqual(details_by_key['vpn']['state'], 'CONNECTED')
        self.assertEqual(details_by_key['github']['state'], 'CONNECTED')
        self.assertEqual(details_by_key['cloud']['state'], 'DISCONNECTED')
        self.assertEqual(details_by_key['slack']['state'], 'DISCONNECTED')

    def test_employee_with_disabled_vpn_distinguished_from_not_provisioned(self):
        """A confirmed disabled VPN access record is marked DISCONNECTED, not missing."""
        emp = Employee.objects.create(
            full_name="Disabled VPN User",
            email="disabledvpn@example.com",
            department="QA",
            status=EmployeeStatus.ACTIVE
        )
        VPNAccess.objects.create(employee=emp, status=VPNAccessStatus.DISABLED)

        detail_url = reverse('employee-detail', kwargs={'pk': emp.id})
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        details_by_key = {s['key']: s for s in response.data['connected_systems']}
        self.assertEqual(details_by_key['vpn']['status'], 'DISABLED')
        self.assertEqual(details_by_key['vpn']['state'], 'DISCONNECTED')
        self.assertFalse(details_by_key['vpn']['is_connected'])


