"""
Automated unit and integration test suite for ReconcileOS Reconciliation Engine.
"""

import uuid
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from apps.employees.models import Employee, EmployeeStatus
from apps.connectors.models import VPNAccess, VPNAccessStatus
from apps.rules.models import Rule, RuleSeverity
from apps.accounts.models import UserProfile, UserRole
from .models import IntegrityViolation, ViolationStatus
from .collectors import (
    StateCollector,
    EmployeeNotFoundException,
    InvalidEmployeeIDException
)
from .engine import ReconciliationEngine


class StateCollectorUnitTests(TestCase):
    """Unit tests for the StateCollector and BaseConnectorStateCollector interface."""

    def setUp(self):
        self.active_emp = Employee.objects.create(
            full_name="Alice Developer",
            email="alice.dev@company.com",
            department="Engineering",
            status=EmployeeStatus.ACTIVE
        )
        self.term_emp = Employee.objects.create(
            full_name="Rahul Kumar",
            email="rahul.kumar@reconcileos.internal",
            department="DevOps & Cloud Integrity",
            status=EmployeeStatus.TERMINATED
        )
        self.unprovisioned_emp = Employee.objects.create(
            full_name="Charlie Unprovisioned",
            email="charlie.unprov@company.com",
            department="Sales",
            status=EmployeeStatus.ACTIVE
        )

        self.vpn_alice = VPNAccess.objects.create(
            employee=self.active_emp,
            status=VPNAccessStatus.DISABLED
        )
        self.vpn_rahul = VPNAccess.objects.create(
            employee=self.term_emp,
            status=VPNAccessStatus.ENABLED
        )

    def test_collect_hr_and_vpn_state_for_employee(self):
        """Test collecting state for Rahul Kumar produces expected dictionary payload."""
        collector = StateCollector()
        payload = collector.collect_employee_state(self.term_emp.id)

        self.assertEqual(payload['employee_id'], str(self.term_emp.id))
        self.assertEqual(payload['employee_name'], "Rahul Kumar")
        self.assertEqual(payload['employee_email'], "rahul.kumar@reconcileos.internal")
        self.assertEqual(payload['department'], "DevOps & Cloud Integrity")
        self.assertEqual(payload['employee_status'], "TERMINATED")
        self.assertIn('collected_at', payload)

        self.assertIn('systems', payload)
        self.assertIn('vpn', payload['systems'])
        vpn_state = payload['systems']['vpn']
        self.assertTrue(vpn_state['connected'])
        self.assertEqual(vpn_state['access_status'], "ENABLED")
        self.assertEqual(vpn_state['record_id'], str(self.vpn_rahul.id))

    def test_collect_state_for_unprovisioned_employee_with_no_vpn_record(self):
        """Test collecting state for employee with no VPN record returns NOT_PROVISIONED state."""
        self.assertFalse(VPNAccess.objects.filter(employee=self.unprovisioned_emp).exists())

        collector = StateCollector()
        payload = collector.collect_employee_state(self.unprovisioned_emp.id)

        self.assertEqual(payload['employee_id'], str(self.unprovisioned_emp.id))
        self.assertEqual(payload['employee_status'], "ACTIVE")
        
        vpn_state = payload['systems']['vpn']
        self.assertFalse(vpn_state['connected'])
        self.assertEqual(vpn_state['access_status'], "NOT_PROVISIONED")
        self.assertIsNone(vpn_state['record_id'])

    def test_collect_state_by_email(self):
        """Test resolving and collecting state by employee email address."""
        collector = StateCollector()
        payload = collector.collect_employee_state("alice.dev@company.com")
        self.assertEqual(payload['employee_name'], "Alice Developer")
        self.assertEqual(payload['systems']['vpn']['access_status'], "DISABLED")

    def test_collect_state_invalid_and_missing_employee_ids(self):
        """Test invalid UUID formats and missing employee IDs raise appropriate exceptions."""
        collector = StateCollector()

        random_uuid = uuid.uuid4()
        with self.assertRaises(EmployeeNotFoundException):
            collector.collect_employee_state(random_uuid)

        with self.assertRaises(InvalidEmployeeIDException):
            collector.collect_employee_state("invalid-id-string-without-at-symbol")

    def test_collect_all_states(self):
        """Test collect_all_states aggregates states for all employees."""
        collector = StateCollector()
        states = collector.collect_all_states()
        self.assertEqual(len(states), 3)


class ReconciliationEngineUnitTests(TestCase):
    """Unit tests for the Reconciliation Engine drift evaluation logic."""

    def setUp(self):
        self.rule = Rule.objects.create(
            rule_code="INV-RULE-001",
            name="Terminated employees must not have VPN access",
            source_system="HR",
            condition_attribute="status",
            condition_value="TERMINATED",
            target_system="VPN",
            expected_attribute="status",
            expected_value="DISABLED",
            severity=RuleSeverity.CRITICAL,
            is_enabled=True
        )

        self.rahul = Employee.objects.create(
            full_name="Rahul Kumar",
            email="rahul.kumar@reconcileos.internal",
            department="DevOps",
            status=EmployeeStatus.TERMINATED
        )
        self.vpn_rahul = VPNAccess.objects.create(
            employee=self.rahul,
            status=VPNAccessStatus.ENABLED
        )

        self.alice = Employee.objects.create(
            full_name="Alice Developer",
            email="alice.dev@company.com",
            department="Engineering",
            status=EmployeeStatus.ACTIVE
        )
        self.vpn_alice = VPNAccess.objects.create(
            employee=self.alice,
            status=VPNAccessStatus.ENABLED
        )

        self.bob = Employee.objects.create(
            full_name="Bob Terminated",
            email="bob.term@company.com",
            department="Sales",
            status=EmployeeStatus.TERMINATED
        )
        self.vpn_bob = VPNAccess.objects.create(
            employee=self.bob,
            status=VPNAccessStatus.DISABLED
        )

    def test_1_matching_state_produces_no_violation(self):
        """1. Test matching/compliant state (TERMINATED + DISABLED) produces no violation."""
        engine = ReconciliationEngine()
        report = engine.evaluate_employee_rules(self.bob.id)

        self.assertEqual(report['violations_detected_count'], 0)
        self.assertFalse(IntegrityViolation.objects.filter(employee=self.bob, status=ViolationStatus.OPEN).exists())

    def test_2_terminated_and_enabled_vpn_produces_violation(self):
        """2. Test TERMINATED + ENABLED VPN produces an OPEN IntegrityViolation."""
        engine = ReconciliationEngine()
        report = engine.evaluate_employee_rules(self.rahul.id)

        self.assertEqual(report['violations_detected_count'], 1)
        self.assertTrue(IntegrityViolation.objects.filter(employee=self.rahul, status=ViolationStatus.OPEN).exists())

    def test_3_active_and_enabled_vpn_does_not_produce_violation(self):
        """3. Test ACTIVE + ENABLED VPN does not produce a violation."""
        engine = ReconciliationEngine()
        report = engine.evaluate_employee_rules(self.alice.id)

        self.assertEqual(report['violations_detected_count'], 0)
        self.assertFalse(IntegrityViolation.objects.filter(employee=self.alice, status=ViolationStatus.OPEN).exists())

    def test_4_violation_contains_correct_expected_and_actual_state(self):
        """4. Test the violation contains correct expected and actual state and severity."""
        engine = ReconciliationEngine()
        engine.evaluate_employee_rules(self.rahul.id)

        violation = IntegrityViolation.objects.get(employee=self.rahul, status=ViolationStatus.OPEN)
        self.assertEqual(violation.rule, self.rule)
        self.assertEqual(violation.affected_system, "VPN")
        self.assertEqual(violation.expected_state, "DISABLED")
        self.assertEqual(violation.actual_state, "ENABLED")
        self.assertEqual(violation.severity, RuleSeverity.CRITICAL)
        self.assertEqual(violation.status, ViolationStatus.OPEN)

    def test_5_running_detection_does_not_modify_vpn_state(self):
        """5. Test running reconciliation detection does NOT modify downstream VPN state."""
        engine = ReconciliationEngine()
        engine.evaluate_employee_rules(self.rahul.id)

        self.vpn_rahul.refresh_from_db()
        self.assertEqual(self.vpn_rahul.status, VPNAccessStatus.ENABLED)

    def test_6_rerunning_detection_is_idempotent_no_duplicate_violations(self):
        """6. Test running detection repeatedly does NOT create duplicate OPEN violations."""
        engine = ReconciliationEngine()
        
        engine.evaluate_employee_rules(self.rahul.id)
        engine.evaluate_employee_rules(self.rahul.id)
        engine.evaluate_employee_rules(self.rahul.id)

        open_count = IntegrityViolation.objects.filter(
            employee=self.rahul,
            rule=self.rule,
            status=ViolationStatus.OPEN
        ).count()
        self.assertEqual(open_count, 1)

    def test_7_resolving_drift_marks_violation_as_resolved(self):
        """7. Test that updating VPN to DISABLED and re-evaluating marks violation as RESOLVED."""
        engine = ReconciliationEngine()
        engine.evaluate_employee_rules(self.rahul.id)
        self.assertTrue(IntegrityViolation.objects.filter(employee=self.rahul, status=ViolationStatus.OPEN).exists())

        self.vpn_rahul.status = VPNAccessStatus.DISABLED
        self.vpn_rahul.save()

        engine.evaluate_employee_rules(self.rahul.id)

        self.assertFalse(IntegrityViolation.objects.filter(employee=self.rahul, status=ViolationStatus.OPEN).exists())
        self.assertTrue(IntegrityViolation.objects.filter(employee=self.rahul, status=ViolationStatus.RESOLVED).exists())


class ReconciliationAPITests(APITestCase):
    """Integration tests for Reconciliation REST API endpoints."""

    def setUp(self):
        self.admin_user = User.objects.create_superuser('admin_rec', 'admin@rec.com', 'admin123')
        UserProfile.objects.create(user=self.admin_user, role=UserRole.ADMIN)
        self.client.force_authenticate(user=self.admin_user)

        self.rule = Rule.objects.create(
            rule_code="INV-RULE-001",
            name="Terminated VPN disabled",
            source_system="HR",
            condition_attribute="status",
            condition_value="TERMINATED",
            target_system="VPN",
            expected_attribute="status",
            expected_value="DISABLED",
            severity=RuleSeverity.CRITICAL,
            is_enabled=True
        )
        self.rahul = Employee.objects.create(
            full_name="Rahul Kumar",
            email="rahul.kumar@reconcileos.internal",
            department="DevOps",
            status=EmployeeStatus.TERMINATED
        )
        self.vpn = VPNAccess.objects.create(
            employee=self.rahul,
            status=VPNAccessStatus.ENABLED
        )

        self.violations_list_url = reverse('integrityviolation-list')
        self.reconciliation_run_url = reverse('reconciliation-run')

    def test_run_reconciliation_api_endpoint(self):
        """Test POST /api/v1/reconciliation/run/ triggers reconciliation audit."""
        response = self.client.post(self.reconciliation_run_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['total_violations_detected'], 1)

    def test_list_violations_api_endpoint(self):
        """Test GET /api/v1/reconciliation/violations/ returns detected violations."""
        engine = ReconciliationEngine()
        engine.evaluate_all()

        response = self.client.get(self.violations_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['employee_name'], "Rahul Kumar")
        self.assertEqual(response.data['results'][0]['expected_state'], "DISABLED")
        self.assertEqual(response.data['results'][0]['actual_state'], "ENABLED")
        self.assertEqual(response.data['results'][0]['severity'], "CRITICAL")
        self.assertEqual(response.data['results'][0]['status'], "OPEN")
