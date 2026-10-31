"""
ReconcileOS Phase 4 — End-to-End Functional Audit Test Suite

Automated verification of Workflows 1–9 using Django test framework and disposable SQLite database:
1. Authentication (valid login, invalid login, logout/missing token, invalid/expired token, role permissions)
2. Employee Lifecycle (terminate active employee, verify audit log with actor/states/metadata, immediate reconciliation, repeat termination idempotency)
3. Violation Detection (integrity violation created once, accurate details, repeated scan does not duplicate OPEN violation)
4. Approval Security (unauthorized roles VIEWER and OPERATOR cannot approve or execute repairs)
5. Repair Lifecycle (ADMIN approval, automated/manual execution through connector adapter, downstream state updated to DISABLED, verification SUCCESS, violation RESOLVED)
6. Failure Handling (simulated connector transient failure, execution log error capture, retry recovery, execution idempotency on already completed plan)
7. Audit Integrity (cryptographic SHA-256 chain verification, tamper detection on altered record, role enforcement on privileged verification endpoint)
8. Connected Systems (connector health checks, latency in ms, clear simulated vs external distinction, ping endpoint)
9. Pagination and Filters (multiple pages, filters, empty results, total counts, bidirectional pagination)
"""

import uuid
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import UserProfile, UserRole
from apps.employees.models import Employee, EmployeeStatus
from apps.connectors.models import (
    VPNAccess, VPNAccessStatus,
    GitHubMembership, GitHubAccessStatus,
    CloudIAMAccess, CloudRole,
    SlackAccount, SlackAccountStatus
)
from apps.connectors.adapters import ConnectorRegistry
from apps.rules.models import Rule, RuleSeverity
from apps.reconciliation.models import IntegrityViolation, ViolationStatus
from apps.workflows.models import RepairPlan, PlanStatus, RepairExecutionLog, RepairVerification
from apps.approvals.models import ApprovalRequest, ApprovalDecision
from apps.audit.models import AuditLog, AuditEventType
from apps.audit.services import AuditLogger


class Phase4EndToEndFunctionalAuditTests(TestCase):
    """
    Complete end-to-end audit test cases covering Workflows 1 through 9.
    """

    def setUp(self):
        self.client = APIClient()

        # 1. Setup RBAC Users
        self.admin_user = User.objects.create_user('audit_admin', 'admin@audit.org', 'Pass123!Admin')
        UserProfile.objects.create(user=self.admin_user, role=UserRole.ADMIN)

        self.operator_user = User.objects.create_user('audit_operator', 'operator@audit.org', 'Pass123!Oper')
        UserProfile.objects.create(user=self.operator_user, role=UserRole.OPERATOR)

        self.viewer_user = User.objects.create_user('audit_viewer', 'viewer@audit.org', 'Pass123!View')
        UserProfile.objects.create(user=self.viewer_user, role=UserRole.VIEWER)

        # 2. Invariant Security Rules
        self.vpn_rule = Rule.objects.create(
            rule_code='INV-RULE-VPN-001',
            name='Terminated Employees Must Not Have VPN Access',
            description='Enforces zero-trust revocation of VPN credentials upon employee termination.',
            source_system='HR',
            condition_attribute='status',
            condition_value='TERMINATED',
            target_system='VPN',
            expected_attribute='status',
            expected_value='DISABLED',
            severity=RuleSeverity.CRITICAL,
            is_enabled=True
        )

        # Ensure failure modes on connector are clean
        self.vpn_connector = None
        try:
            from apps.connectors.adapters import ConnectorRegistry
            self.vpn_connector = ConnectorRegistry.get_connector('vpn')
            if self.vpn_connector:
                self.vpn_connector.fail_next_n_attempts = 0
                self.vpn_connector.fail_with_state_applied = False
        except Exception:
            pass

    def tearDown(self):
        if self.vpn_connector:
            self.vpn_connector.fail_next_n_attempts = 0
            self.vpn_connector.fail_with_state_applied = False

    def _login(self, username, password):
        """Helper to login and set Bearer auth header."""
        res = self.client.post('/api/v1/auth/login/', {'username': username, 'password': password})
        if res.status_code == status.HTTP_200_OK:
            self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['access']}")
        return res

    def _logout(self):
        """Helper to clear client credentials."""
        self.client.credentials()

    # =========================================================================
    # WORKFLOW 1: Authentication & RBAC Access
    # =========================================================================
    def test_workflow_1_authentication(self):
        """
        Verify:
        - Valid login returns 200, JWT tokens, and user profile role.
        - Invalid login returns 401.
        - Missing or invalid token returns 401.
        - VIEWER role can read but cannot perform privileged mutations (403).
        - OPERATOR role can scan reconciliation but cannot approve/execute repairs (403).
        - ADMIN role has full privileged access.
        """
        # 1a. Invalid Login
        res_bad = self.client.post('/api/v1/auth/login/', {'username': 'audit_admin', 'password': 'WrongPassword!'})
        self.assertEqual(res_bad.status_code, status.HTTP_401_UNAUTHORIZED)

        # 1b. Valid Login (Admin)
        res_admin = self._login('audit_admin', 'Pass123!Admin')
        self.assertEqual(res_admin.status_code, status.HTTP_200_OK)
        self.assertIn('access', res_admin.data)
        self.assertIn('refresh', res_admin.data)
        self.assertEqual(res_admin.data['user']['role'], UserRole.ADMIN)

        # 1c. Profile endpoint with valid token
        res_me = self.client.get('/api/v1/auth/me/')
        self.assertEqual(res_me.status_code, status.HTTP_200_OK)
        self.assertEqual(res_me.data['username'], 'audit_admin')

        # 1d. Unauthenticated request / Logout
        self._logout()
        res_unauth = self.client.get('/api/v1/auth/me/')
        self.assertEqual(res_unauth.status_code, status.HTTP_401_UNAUTHORIZED)

        # 1e. Expired / Invalid token
        self.client.credentials(HTTP_AUTHORIZATION='Bearer completely.bogus.jwttoken')
        res_bogus = self.client.get('/api/v1/auth/me/')
        self.assertEqual(res_bogus.status_code, status.HTTP_401_UNAUTHORIZED)
        self._logout()

        # 1f. Viewer Restrictions
        self._login('audit_viewer', 'Pass123!View')
        # Allowed read
        res_v_read = self.client.get('/api/v1/employees/')
        self.assertEqual(res_v_read.status_code, status.HTTP_200_OK)
        # Denied privileged action: run reconciliation
        res_v_run = self.client.post('/api/v1/reconciliation/run/')
        self.assertEqual(res_v_run.status_code, status.HTTP_403_FORBIDDEN)
        # Denied privileged action: rule toggle
        res_v_toggle = self.client.post(f'/api/v1/rules/{self.vpn_rule.id}/toggle/')
        self.assertEqual(res_v_toggle.status_code, status.HTTP_403_FORBIDDEN)
        self._logout()

        # 1g. Operator Permissions & Restrictions
        self._login('audit_operator', 'Pass123!Oper')
        # Allowed: trigger reconciliation
        res_op_run = self.client.post('/api/v1/reconciliation/run/')
        self.assertEqual(res_op_run.status_code, status.HTTP_200_OK)
        # Denied: rule toggle (requires admin)
        res_op_toggle = self.client.post(f'/api/v1/rules/{self.vpn_rule.id}/toggle/')
        self.assertEqual(res_op_toggle.status_code, status.HTTP_403_FORBIDDEN)
        self._logout()

    # =========================================================================
    # WORKFLOW 2: Employee Lifecycle (Termination & Audit Event)
    # =========================================================================
    def test_workflow_2_employee_lifecycle(self):
        """
        Verify:
        - Terminating an employee updates status to TERMINATED.
        - Cryptographic audit event EMPLOYEE_TERMINATED is recorded with actor, previous state, new state, and reason.
        - Immediate reconciliation is performed and returned in response.
        - Repeating the termination request is idempotent and does not create duplicate audit events.
        """
        self._login('audit_admin', 'Pass123!Admin')

        # Create active employee with active VPN access
        emp = Employee.objects.create(
            full_name='Alice Smith',
            email='alice.smith@audit.org',
            department='Engineering',
            status=EmployeeStatus.ACTIVE
        )
        VPNAccess.objects.create(employee=emp, status=VPNAccessStatus.ENABLED)

        initial_audit_count = AuditLog.objects.filter(employee=emp).count()

        # Terminate employee via API
        term_res = self.client.post(
            f'/api/v1/employees/{emp.id}/terminate/',
            {'reason': 'Voluntary resignation notice served'}
        )
        self.assertEqual(term_res.status_code, status.HTTP_200_OK)
        self.assertTrue(term_res.data['status_changed'])
        self.assertEqual(term_res.data['employee']['status'], EmployeeStatus.TERMINATED)
        self.assertIn('reconciliation', term_res.data)
        self.assertEqual(term_res.data['reconciliation']['status'], 'completed')
        self.assertGreaterEqual(term_res.data['reconciliation']['violations_detected_count'], 1)

        # Verify employee record in DB
        emp.refresh_from_db()
        self.assertEqual(emp.status, EmployeeStatus.TERMINATED)

        # Verify lifecycle audit event recorded
        term_audit = AuditLog.objects.filter(
            employee=emp,
            event_type=AuditEventType.EMPLOYEE_TERMINATED
        ).first()
        self.assertIsNotNone(term_audit)
        self.assertEqual(term_audit.actor, 'audit_admin')
        self.assertEqual(term_audit.previous_state, EmployeeStatus.ACTIVE)
        self.assertEqual(term_audit.new_state, EmployeeStatus.TERMINATED)
        self.assertEqual(term_audit.additional_metadata.get('reason'), 'Voluntary resignation notice served')
        self.assertTrue(term_audit.current_hash)

        # Verify Repeat Termination Request (Idempotency)
        term_res_repeat = self.client.post(
            f'/api/v1/employees/{emp.id}/terminate/',
            {'reason': 'Repeated termination call'}
        )
        self.assertEqual(term_res_repeat.status_code, status.HTTP_200_OK)
        self.assertFalse(term_res_repeat.data['status_changed'])
        self.assertEqual(term_res_repeat.data['message'], 'Employee is already terminated.')

        # Ensure no duplicate EMPLOYEE_TERMINATED audit event was added
        term_audit_count = AuditLog.objects.filter(
            employee=emp,
            event_type=AuditEventType.EMPLOYEE_TERMINATED
        ).count()
        self.assertEqual(term_audit_count, 1)

        self._logout()

    # =========================================================================
    # WORKFLOW 3: Violation Detection
    # =========================================================================
    def test_workflow_3_violation_detection(self):
        """
        Verify:
        - When employee is TERMINATED but VPN is ENABLED, reconciliation creates an OPEN violation.
        - Violation details accurately capture affected_system='VPN', expected='DISABLED', actual='ENABLED'.
        - Subsequent reconciliation scans do not create duplicate OPEN violations.
        """
        self._login('audit_admin', 'Pass123!Admin')

        emp = Employee.objects.create(
            full_name='Bob Jones',
            email='bob.jones@audit.org',
            department='Sales',
            status=EmployeeStatus.TERMINATED
        )
        VPNAccess.objects.create(employee=emp, status=VPNAccessStatus.ENABLED)

        # Run reconciliation
        scan_res = self.client.post('/api/v1/reconciliation/run/', {'employee_id': str(emp.id)})
        self.assertEqual(scan_res.status_code, status.HTTP_200_OK)

        # Query violations
        violations = IntegrityViolation.objects.filter(employee=emp, affected_system='VPN')
        self.assertEqual(violations.count(), 1)

        viol = violations.first()
        self.assertEqual(viol.status, ViolationStatus.OPEN)
        self.assertEqual(viol.expected_state, 'DISABLED')
        self.assertEqual(viol.actual_state, 'ENABLED')
        self.assertEqual(viol.severity, RuleSeverity.CRITICAL)

        # Run reconciliation a second time
        scan_res_2 = self.client.post('/api/v1/reconciliation/run/', {'employee_id': str(emp.id)})
        self.assertEqual(scan_res_2.status_code, status.HTTP_200_OK)

        # Verify violation is still single (not duplicated)
        violations_after = IntegrityViolation.objects.filter(employee=emp, affected_system='VPN')
        self.assertEqual(violations_after.count(), 1)
        self.assertEqual(violations_after.first().id, viol.id)

        self._logout()

    # =========================================================================
    # WORKFLOW 4: Approval Security
    # =========================================================================
    def test_workflow_4_approval_security(self):
        """
        Verify:
        - VIEWER and OPERATOR cannot approve or reject pending approvals (403 Forbidden).
        - VIEWER and OPERATOR cannot execute repair plans (403 Forbidden).
        """
        emp = Employee.objects.create(
            full_name='Charlie Brown',
            email='charlie.b@audit.org',
            department='Finance',
            status=EmployeeStatus.TERMINATED
        )
        VPNAccess.objects.create(employee=emp, status=VPNAccessStatus.ENABLED)
        viol = IntegrityViolation.objects.create(
            employee=emp, rule=self.vpn_rule, affected_system='VPN',
            expected_state='DISABLED', actual_state='ENABLED', status=ViolationStatus.OPEN
        )
        plan = RepairPlan.objects.create(
            employee=emp, violation=viol, target_system='VPN',
            action='DISABLE VPN ACCESS', reason='Employee is TERMINATED', risk_level='CRITICAL',
            status=PlanStatus.PENDING
        )
        approval_req = ApprovalRequest.objects.create(
            repair_plan=plan, decision=ApprovalDecision.PENDING
        )

        # 4a. Viewer attempts
        self._login('audit_viewer', 'Pass123!View')
        res_v_app = self.client.post(f'/api/v1/approvals/{approval_req.id}/approve/')
        self.assertEqual(res_v_app.status_code, status.HTTP_403_FORBIDDEN)

        res_v_rej = self.client.post(f'/api/v1/approvals/{approval_req.id}/reject/')
        self.assertEqual(res_v_rej.status_code, status.HTTP_403_FORBIDDEN)

        res_v_exec = self.client.post(f'/api/v1/workflows/plans/{plan.id}/execute/')
        self.assertEqual(res_v_exec.status_code, status.HTTP_403_FORBIDDEN)
        self._logout()

        # 4b. Operator attempts
        self._login('audit_operator', 'Pass123!Oper')
        res_op_app = self.client.post(f'/api/v1/approvals/{approval_req.id}/approve/')
        self.assertEqual(res_op_app.status_code, status.HTTP_403_FORBIDDEN)

        res_op_exec = self.client.post(f'/api/v1/workflows/plans/{plan.id}/execute/')
        self.assertEqual(res_op_exec.status_code, status.HTTP_403_FORBIDDEN)
        self._logout()

        # Ensure plan and approval remain untouched
        approval_req.refresh_from_db()
        plan.refresh_from_db()
        self.assertEqual(approval_req.decision, ApprovalDecision.PENDING)
        self.assertEqual(plan.status, PlanStatus.PENDING)

    # =========================================================================
    # WORKFLOW 5: Repair Lifecycle (Approval -> Execution -> Verification -> Resolution)
    # =========================================================================
    def test_workflow_5_repair_lifecycle(self):
        """
        Verify:
        - ADMIN approves pending approval request.
        - Execution updates downstream connector state (VPN becomes DISABLED).
        - Empirical verification confirms DISABLED state and records SUCCESS.
        - Violation transitions from OPEN to RESOLVED.
        - Plan status transitions to SUCCESS / COMPLETED.
        """
        self._login('audit_admin', 'Pass123!Admin')

        emp = Employee.objects.create(
            full_name='Diana Prince',
            email='diana.prince@audit.org',
            department='Legal',
            status=EmployeeStatus.TERMINATED
        )
        vpn = VPNAccess.objects.create(employee=emp, status=VPNAccessStatus.ENABLED)
        viol = IntegrityViolation.objects.create(
            employee=emp, rule=self.vpn_rule, affected_system='VPN',
            expected_state='DISABLED', actual_state='ENABLED', status=ViolationStatus.OPEN
        )
        plan = RepairPlan.objects.create(
            employee=emp, violation=viol, target_system='VPN',
            action='DISABLE VPN ACCESS', reason='Employee is TERMINATED', risk_level='CRITICAL',
            status=PlanStatus.PENDING
        )
        approval_req = ApprovalRequest.objects.create(
            repair_plan=plan, decision=ApprovalDecision.PENDING
        )

        # Approve and execute repair
        res_approve = self.client.post(
            f'/api/v1/approvals/{approval_req.id}/approve/',
            {'comment': 'Security audit authorization'}
        )
        self.assertEqual(res_approve.status_code, status.HTTP_200_OK)

        # Refresh instances
        approval_req.refresh_from_db()
        plan.refresh_from_db()
        viol.refresh_from_db()
        vpn.refresh_from_db()

        # Assertions
        self.assertEqual(approval_req.decision, ApprovalDecision.APPROVED)
        self.assertIn(plan.status, [PlanStatus.SUCCESS, PlanStatus.COMPLETED])
        self.assertEqual(vpn.status, VPNAccessStatus.DISABLED)
        self.assertEqual(viol.status, ViolationStatus.RESOLVED)

        # Verify verification record
        verification = RepairVerification.objects.filter(repair_plan=plan).first()
        self.assertIsNotNone(verification)
        self.assertEqual(verification.result, 'VERIFIED')
        self.assertEqual(verification.actual_state, 'DISABLED')

        self._logout()

    # =========================================================================
    # WORKFLOW 6: Failure Handling & Idempotency
    # =========================================================================
    def test_workflow_6_failure_handling(self):
        """
        Verify:
        - Connector transient failures are caught, logged, and bounded retries are applied.
        - When transient failure occurs on Attempt #1, retry occurs and succeeds on Attempt #2.
        - Execution logs accurately document both the failed attempt and the successful recovery attempt.
        - Executing an already COMPLETED plan is rejected (idempotency guard).
        """
        self._login('audit_admin', 'Pass123!Admin')

        emp = Employee.objects.create(
            full_name='Evan Wright',
            email='evan.wright@audit.org',
            department='DevOps',
            status=EmployeeStatus.TERMINATED
        )
        vpn = VPNAccess.objects.create(employee=emp, status=VPNAccessStatus.ENABLED)
        viol = IntegrityViolation.objects.create(
            employee=emp, rule=self.vpn_rule, affected_system='VPN',
            expected_state='DISABLED', actual_state='ENABLED', status=ViolationStatus.OPEN
        )
        plan = RepairPlan.objects.create(
            employee=emp, violation=viol, target_system='VPN',
            action='DISABLE VPN ACCESS', reason='Employee is TERMINATED', risk_level='CRITICAL',
            status=PlanStatus.PENDING
        )
        approval_req = ApprovalRequest.objects.create(
            repair_plan=plan, decision=ApprovalDecision.PENDING
        )

        # 6a. Simulate 1 transient failure on attempt #1 (cleared on attempt #2)
        self.vpn_connector.set_simulated_failure(fail_next_n=1, apply_state_first=False)

        # Approve and execute (auto_retry handles the recovery on attempt #2)
        res_approve = self.client.post(
            f'/api/v1/approvals/{approval_req.id}/approve/',
            {'comment': 'Testing transient failure recovery'}
        )
        self.assertEqual(res_approve.status_code, status.HTTP_200_OK)

        # Plan successfully completed after retry
        plan.refresh_from_db()
        vpn.refresh_from_db()
        self.assertIn(plan.status, [PlanStatus.SUCCESS, PlanStatus.COMPLETED])
        self.assertEqual(vpn.status, VPNAccessStatus.DISABLED)

        # Verify execution logs recorded BOTH Attempt #1 (FAILED) and Attempt #2 (SUCCESS)
        exec_logs = RepairExecutionLog.objects.filter(repair_plan=plan).order_by('attempt_number')
        self.assertEqual(exec_logs.count(), 2)

        # Attempt 1: Failed with simulated gateway error
        log_attempt_1 = exec_logs[0]
        self.assertEqual(log_attempt_1.attempt_number, 1)
        self.assertEqual(log_attempt_1.status, 'FAILED')
        self.assertIn('503', log_attempt_1.error_details)

        # Attempt 2: Recovered and succeeded
        log_attempt_2 = exec_logs[1]
        self.assertEqual(log_attempt_2.attempt_number, 2)
        self.assertEqual(log_attempt_2.status, 'SUCCESS')

        # 6b. Idempotency guard: Attempting to execute an already COMPLETED plan
        res_repeat_exec = self.client.post(f'/api/v1/workflows/plans/{plan.id}/execute/')
        self.assertEqual(res_repeat_exec.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already', res_repeat_exec.data.get('message', '').lower())

        self._logout()

    # =========================================================================
    # WORKFLOW 7: Audit Integrity & Cryptographic Chain
    # =========================================================================
    def test_workflow_7_audit_integrity(self):
        """
        Verify:
        - Cryptographic SHA-256 chain is valid on uncorrupted records.
        - /api/v1/audit/logs/verify_chain/ returns 200 OK and is_valid=True.
        - Modifying a past audit log record causes verify_chain to detect tampering (409 Conflict).
        - VIEWER is denied access to verify_chain (403 Forbidden).
        """
        self._login('audit_admin', 'Pass123!Admin')

        # Generate audit records
        emp = Employee.objects.create(full_name='Grace Hopper', email='grace@navy.mil', department='R&D')
        AuditLogger.log_event(
            event_type=AuditEventType.EMPLOYEE_TERMINATED,
            actor='audit_admin',
            employee=emp,
            system='HR',
            action='TERMINATE_EMPLOYEE',
            previous_state=EmployeeStatus.ACTIVE,
            new_state=EmployeeStatus.TERMINATED,
            result='SUCCESS'
        )
        AuditLogger.log_event(
            event_type=AuditEventType.RULE_EVALUATED,
            actor='audit_admin',
            employee=emp,
            system='VPN',
            action='EVALUATE_RULE',
            previous_state='TERMINATED',
            new_state='COMPLIANT',
            result='SUCCESS'
        )

        # Verify clean chain via API
        res_verify = self.client.get('/api/v1/audit/logs/verify_chain/')
        self.assertEqual(res_verify.status_code, status.HTTP_200_OK)
        self.assertTrue(res_verify.data['is_valid'])

        # Tamper test: Corrupt an audit record directly in the DB
        first_record = AuditLog.objects.order_by('id').first()
        original_action = first_record.action
        AuditLog.objects.filter(id=first_record.id).update(action='TAMPERED_ACTION_MALICIOUS')

        # Verify chain now fails with 409 CONFLICT and detects tamper
        res_tamper = self.client.get('/api/v1/audit/logs/verify_chain/')
        self.assertEqual(res_tamper.status_code, status.HTTP_409_CONFLICT)
        self.assertFalse(res_tamper.data['is_valid'])
        self.assertIn('tamper', res_tamper.data['message'].lower())

        # Restore original action
        AuditLog.objects.filter(id=first_record.id).update(action=original_action)
        res_restored = self.client.get('/api/v1/audit/logs/verify_chain/')
        self.assertEqual(res_restored.status_code, status.HTTP_200_OK)
        self.assertTrue(res_restored.data['is_valid'])

        # Role enforcement: Viewer cannot call verify_chain
        self._logout()
        self._login('audit_viewer', 'Pass123!View')
        res_v_chain = self.client.get('/api/v1/audit/logs/verify_chain/')
        self.assertEqual(res_v_chain.status_code, status.HTTP_403_FORBIDDEN)
        self._logout()

    # =========================================================================
    # WORKFLOW 8: Connected Systems Health & Distinction
    # =========================================================================
    def test_workflow_8_connected_systems(self):
        """
        Verify:
        - GET /api/v1/connectors/health/ returns all 5 connected systems (HR, VPN, GitHub, Cloud, Slack).
        - Latency is numeric and measured in ms.
        - Connectors explicitly report whether they are simulated vs live external.
        - Ping endpoint returns 200 OK.
        """
        self._login('audit_admin', 'Pass123!Admin')

        res_health = self.client.get('/api/v1/connectors/health/')
        self.assertEqual(res_health.status_code, status.HTTP_200_OK)
        self.assertEqual(res_health.data['status'], 'success')

        systems = res_health.data['systems']
        self.assertIn('hr', systems)
        self.assertIn('vpn', systems)
        self.assertIn('github', systems)
        self.assertIn('cloud', systems)
        self.assertIn('slack', systems)

        # Check VPN details
        vpn_info = systems['vpn']
        self.assertIn('status', vpn_info)
        self.assertIn('latency_ms', vpn_info)
        self.assertIsInstance(vpn_info['latency_ms'], (int, float))
        self.assertTrue(vpn_info.get('is_simulated'))
        self.assertFalse(vpn_info.get('is_live_external'))

        # Check GitHub details (database fallback mode)
        gh_info = systems['github']
        self.assertTrue(gh_info.get('is_simulated'))
        self.assertFalse(gh_info.get('is_live_external'))

        # Ping VPN connector
        res_ping = self.client.post('/api/v1/connectors/vpn/ping/')
        self.assertEqual(res_ping.status_code, status.HTTP_200_OK)

        self._logout()

    # =========================================================================
    # WORKFLOW 9: Pagination and Filters
    # =========================================================================
    def test_workflow_9_pagination_and_filters(self):
        """
        Verify:
        - Pagination on /api/v1/employees/ returns count, next, previous, results.
        - Multiple pages work (page 1 -> page 2 -> page 1) using standard PAGE_SIZE=20.
        - Filtering by status produces exact subset matching database.
        - Filtering by non-matching criteria produces count=0, results=[].
        - Filtering with invalid choice returns HTTP 400 Bad Request.
        """
        self._login('audit_admin', 'Pass123!Admin')

        # Clean existing test employees to have precise counts
        Employee.objects.all().delete()

        # Create 20 Active, 5 Terminated (Total: 25 employees)
        for i in range(20):
            Employee.objects.create(
                full_name=f'Active User {i}',
                email=f'active{i}@test.com',
                department='Engineering',
                status=EmployeeStatus.ACTIVE
            )
        for i in range(5):
            Employee.objects.create(
                full_name=f'Terminated User {i}',
                email=f'term{i}@test.com',
                department='Sales',
                status=EmployeeStatus.TERMINATED
            )

        # 9a. Page 1 (PAGE_SIZE=20)
        res_p1 = self.client.get('/api/v1/employees/?page=1')
        self.assertEqual(res_p1.status_code, status.HTTP_200_OK)
        self.assertEqual(res_p1.data['count'], 25)
        self.assertEqual(len(res_p1.data['results']), 20)
        self.assertIsNotNone(res_p1.data['next'])
        self.assertIsNone(res_p1.data['previous'])

        # 9b. Page 2 (Remaining 5 records)
        res_p2 = self.client.get('/api/v1/employees/?page=2')
        self.assertEqual(res_p2.status_code, status.HTTP_200_OK)
        self.assertEqual(res_p2.data['count'], 25)
        self.assertEqual(len(res_p2.data['results']), 5)
        self.assertIsNone(res_p2.data['next'])
        self.assertIsNotNone(res_p2.data['previous'])

        # 9c. Navigate back to Page 1
        res_p1_back = self.client.get('/api/v1/employees/?page=1')
        self.assertEqual(res_p1_back.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_p1_back.data['results']), 20)

        # 9d. Filtering by status=TERMINATED (5 total records -> 1 page)
        res_term = self.client.get('/api/v1/employees/?status=TERMINATED')
        self.assertEqual(res_term.status_code, status.HTTP_200_OK)
        self.assertEqual(res_term.data['count'], 5)
        self.assertEqual(len(res_term.data['results']), 5)
        for item in res_term.data['results']:
            self.assertEqual(item['status'], EmployeeStatus.TERMINATED)

        # 9e. Filtering by valid field with no matches (department='NonExistentDept')
        res_empty = self.client.get('/api/v1/employees/?department=NonExistentDept')
        self.assertEqual(res_empty.status_code, status.HTTP_200_OK)
        self.assertEqual(res_empty.data['count'], 0)
        self.assertEqual(len(res_empty.data['results']), 0)

        # 9f. Strict choice validation: invalid status value returns 400
        res_invalid = self.client.get('/api/v1/employees/?status=INVALID_STATUS')
        self.assertEqual(res_invalid.status_code, status.HTTP_400_BAD_REQUEST)

        self._logout()
