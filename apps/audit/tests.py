"""
Comprehensive Unit & Integration Test Suite for ReconcileOS Audit Logging System.
"""

import uuid
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from apps.employees.models import Employee
from apps.rules.models import Rule, RuleSeverity
from apps.connectors.models import VPNAccess, VPNAccessStatus
from apps.reconciliation.engine import ReconciliationEngine
from apps.reconciliation.models import IntegrityViolation, ViolationStatus
from apps.workflows.planner import RepairPlanner
from apps.workflows.models import RepairPlan, PlanStatus
from apps.approvals.services import ApprovalService
from apps.approvals.models import ApprovalRequest, ApprovalDecision
from apps.workflows.executor import RepairExecutor
from apps.audit.models import AuditLog, AuditEventType
from apps.audit.services import AuditLogger


class AuditLogModelTestCase(TestCase):
    def setUp(self):
        self.employee = Employee.objects.create(
            full_name="Alice Smith",
            email="alice@example.com",
            department="Engineering",
            status="TERMINATED"
        )

    def test_create_audit_log_record(self):
        log = AuditLogger.log_event(
            event_type=AuditEventType.RULE_EVALUATED,
            actor="TestEngine",
            employee=self.employee,
            system="VPN",
            action="EVALUATE_RULE",
            previous_state="ENABLED",
            new_state="DISABLED",
            result="DRIFT_DETECTED",
            additional_metadata={"rule_code": "INV-RULE-001"}
        )
        self.assertIsNotNone(log.id)
        self.assertIsNotNone(log.current_hash)
        self.assertEqual(log.previous_hash, '0' * 64)

    def test_append_only_prevent_update(self):
        log = AuditLogger.log_event(
            event_type=AuditEventType.VIOLATION_DETECTED,
            actor="TestEngine",
            employee=self.employee,
            system="VPN",
            result="DRIFT_DETECTED"
        )
        log.actor = "Hacker"
        with self.assertRaises(ValidationError) as ctx:
            log.save()
        self.assertIn("append-only and cannot be updated", str(ctx.exception))

    def test_append_only_prevent_delete(self):
        log = AuditLogger.log_event(
            event_type=AuditEventType.VIOLATION_DETECTED,
            actor="TestEngine",
            employee=self.employee,
            system="VPN",
            result="DRIFT_DETECTED"
        )
        with self.assertRaises(ValidationError) as ctx:
            log.delete()
        self.assertIn("append-only and cannot be deleted", str(ctx.exception))

    def test_tamper_evident_hash_chain_integrity(self):
        # Create 3 chained audit logs
        log1 = AuditLogger.log_event(
            event_type=AuditEventType.RULE_EVALUATED,
            actor="Engine",
            employee=self.employee,
            system="VPN",
            result="EVALUATED"
        )
        log2 = AuditLogger.log_event(
            event_type=AuditEventType.VIOLATION_DETECTED,
            actor="Engine",
            employee=self.employee,
            system="VPN",
            result="DRIFT_DETECTED"
        )
        log3 = AuditLogger.log_event(
            event_type=AuditEventType.REPAIR_PLAN_CREATED,
            actor="Planner",
            employee=self.employee,
            system="VPN",
            result="PLAN_CREATED"
        )

        self.assertEqual(log2.previous_hash, log1.current_hash)
        self.assertEqual(log3.previous_hash, log2.current_hash)

        # Verify intact chain
        is_valid, msg, details = AuditLogger.verify_chain_integrity()
        self.assertTrue(is_valid)
        self.assertEqual(details["total_records"], 3)

        # Direct DB bypass edit to simulate tamper
        AuditLog.objects.filter(pk=log2.pk).update(action="TAMPERED_BY_SQL")

        # Re-verify chain -> must detect tamper!
        is_valid_after_tamper, msg_tamper, details_tamper = AuditLogger.verify_chain_integrity()
        self.assertFalse(is_valid_after_tamper)
        self.assertIn("Tamper detected", msg_tamper)
        self.assertEqual(details_tamper["tampered_record_id"], str(log2.id))


class AuditLogAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='admin_audit', password='password123')
        self.client.force_authenticate(user=self.user)

        self.employee = Employee.objects.create(
            full_name="Bob Jones",
            email="bob@example.com",
            department="Operations",
            status="TERMINATED"
        )
        self.log1 = AuditLogger.log_event(
            event_type=AuditEventType.RULE_EVALUATED,
            actor="Engine",
            employee=self.employee,
            system="VPN",
            result="COMPLIANT"
        )

    def test_get_audit_logs_list(self):
        response = self.client.get('/api/v1/audit/logs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['event_type'], AuditEventType.RULE_EVALUATED)

    def test_verify_chain_api_endpoint(self):
        response = self.client.get('/api/v1/audit/logs/verify_chain/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_valid'])
        self.assertIn("verified", response.data['message'].lower())

    def test_disallow_post_put_delete_api(self):
        post_resp = self.client.post('/api/v1/audit/logs/', {'event_type': 'test'})
        self.assertEqual(post_resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        put_resp = self.client.put(f'/api/v1/audit/logs/{self.log1.id}/', {'actor': 'malicious'})
        self.assertEqual(put_resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        del_resp = self.client.delete(f'/api/v1/audit/logs/{self.log1.id}/')
        self.assertEqual(del_resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class LifecycleAuditIntegrationTestCase(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(username='admin_sec', password='password123')
        self.employee = Employee.objects.create(
            full_name="Charlie Brown",
            email="charlie@example.com",
            department="DevOps",
            status="TERMINATED"
        )
        self.vpn_access = VPNAccess.objects.create(
            employee=self.employee,
            status=VPNAccessStatus.ENABLED
        )
        self.rule = Rule.objects.create(
            rule_code="INV-RULE-TEST",
            name="Terminated Employee VPN Access Invariant",
            description="Terminated employees must have VPN access disabled",
            source_system="HR",
            condition_attribute="status",
            condition_value="TERMINATED",
            target_system="VPN",
            expected_attribute="status",
            expected_value="DISABLED",
            severity=RuleSeverity.HIGH,
            is_enabled=True
        )

    def test_full_reconciliation_workflow_audit_trail(self):
        correlation_id = str(uuid.uuid4())

        # 1. Evaluate Reconciliation Engine
        engine = ReconciliationEngine()
        report = engine.evaluate_employee_rules(self.employee, correlation_id=correlation_id)
        self.assertEqual(report['violations_detected_count'], 1)

        violation = IntegrityViolation.objects.get(employee=self.employee, rule=self.rule)

        # 2. Plan Repair
        planner = RepairPlanner()
        plan, created = planner.plan_for_violation(violation, correlation_id=correlation_id)
        self.assertTrue(created)

        # 3. Approve Repair Request
        approval_req = ApprovalRequest.objects.get(repair_plan=plan)
        ApprovalService.approve_request(approval_req, decided_by=self.admin_user, comment="Approved for auto-remediation", correlation_id=correlation_id)
        plan.refresh_from_db()

        # 4. Execute Repair & Post-Repair Verification
        executor = RepairExecutor()
        exec_log = executor.execute_plan(plan, executed_by=self.admin_user, correlation_id=correlation_id)
        self.assertEqual(exec_log.status, "SUCCESS")

        # 5. Assert Audit Log Entries
        audit_events = list(AuditLog.objects.filter(correlation_id=correlation_id).order_by('timestamp', 'id'))
        event_types = [e.event_type for e in audit_events]

        self.assertIn(AuditEventType.RULE_EVALUATED, event_types)
        self.assertIn(AuditEventType.VIOLATION_DETECTED, event_types)
        self.assertIn(AuditEventType.REPAIR_PLAN_CREATED, event_types)
        self.assertIn(AuditEventType.APPROVAL_REQUESTED, event_types)
        self.assertIn(AuditEventType.REPAIR_APPROVED, event_types)
        self.assertIn(AuditEventType.REPAIR_EXECUTED, event_types)
        self.assertIn(AuditEventType.VERIFICATION_PERFORMED, event_types)
        self.assertIn(AuditEventType.VIOLATION_RESOLVED, event_types)

        # Verify cryptographic chain integrity across generated trail
        is_valid, msg, details = AuditLogger.verify_chain_integrity()
        self.assertTrue(is_valid)

    def test_repair_rejection_audit_trail(self):
        correlation_id = str(uuid.uuid4())

        engine = ReconciliationEngine()
        engine.evaluate_employee_rules(self.employee, correlation_id=correlation_id)

        violation = IntegrityViolation.objects.get(employee=self.employee, rule=self.rule)
        planner = RepairPlanner()
        plan, _ = planner.plan_for_violation(violation, correlation_id=correlation_id)

        approval_req = ApprovalRequest.objects.get(repair_plan=plan)
        ApprovalService.reject_request(approval_req, decided_by=self.admin_user, comment="Risk too high", correlation_id=correlation_id)

        audit_events = list(AuditLog.objects.filter(correlation_id=correlation_id).order_by('timestamp', 'id'))
        event_types = [e.event_type for e in audit_events]

        self.assertIn(AuditEventType.REPAIR_REJECTED, event_types)

        is_valid, msg, details = AuditLogger.verify_chain_integrity()
        self.assertTrue(is_valid)
