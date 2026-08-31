"""
Reconciliation Engine Core for ReconcileOS.

Evaluates multi-system identity state against active invariant security rules
to detect authorization drift and record integrity violations without mutating
downstream target system states.
"""

import logging
import uuid
from django.utils import timezone
from apps.employees.models import Employee
from apps.rules.models import Rule
from apps.audit.services import AuditLogger
from apps.audit.models import AuditEventType
from .models import IntegrityViolation, ViolationStatus
from .collectors import StateCollector

logger = logging.getLogger(__name__)


class ReconciliationEngine:
    """
    Core Reconciliation Engine service class.
    
    Orchestrates state collection, rule evaluation, and drift detection.
    """

    def __init__(self, state_collector=None):
        self.state_collector = state_collector or StateCollector()

    def evaluate_employee_rules(self, employee_id_or_email, correlation_id: str = None) -> dict:
        """
        Evaluates active rules against the collected multi-system state for a single employee.
        
        Returns a summary report dictionary containing:
        - employee details
        - rules_evaluated count
        - violations_detected list
        - violations_resolved list
        """
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        collected_state = self.state_collector.collect_employee_state(employee_id_or_email)
        employee_id = collected_state['employee_id']
        employee_status = collected_state['employee_status']
        employee_obj = Employee.objects.get(pk=employee_id)

        active_rules = Rule.objects.filter(is_enabled=True)
        detected_violations = []
        resolved_violations = []

        for rule in active_rules:
            # Check if source condition is met (e.g. HR status == 'TERMINATED')
            if not rule.matches_condition(employee_status):
                # Audit event: Rule evaluated (condition not matched)
                AuditLogger.log_event(
                    event_type=AuditEventType.RULE_EVALUATED,
                    actor='ReconciliationEngine',
                    employee=employee_obj,
                    system=rule.target_system,
                    action='EVALUATE_RULE',
                    previous_state=employee_status,
                    new_state='CONDITION_NOT_MET',
                    result='NOT_MATCHED',
                    correlation_id=correlation_id,
                    additional_metadata={
                        'rule_code': rule.rule_code,
                        'source_system': rule.source_system,
                        'condition_attribute': rule.condition_attribute,
                        'condition_value': rule.condition_value,
                    }
                )

                # Source condition not met; if any OPEN violation exists for this rule+employee, mark RESOLVED
                open_viols = IntegrityViolation.objects.filter(
                    employee=employee_obj,
                    rule=rule,
                    status=ViolationStatus.OPEN
                )
                for v in open_viols:
                    v.status = ViolationStatus.RESOLVED
                    v.save(update_fields=['status', 'updated_at'])
                    resolved_violations.append(v)

                    # Audit event: Violation resolved
                    AuditLogger.log_event(
                        event_type=AuditEventType.VIOLATION_RESOLVED,
                        actor='ReconciliationEngine',
                        employee=employee_obj,
                        system=rule.target_system,
                        action='RESOLVE_VIOLATION',
                        previous_state=ViolationStatus.OPEN,
                        new_state=ViolationStatus.RESOLVED,
                        result='VIOLATION_RESOLVED',
                        correlation_id=correlation_id,
                        additional_metadata={
                            'violation_id': str(v.id),
                            'rule_code': rule.rule_code,
                            'reason': 'Source condition no longer matched'
                        }
                    )
                continue

            # Source condition is met! Inspect target system actual state
            target_sys_key = rule.target_system.lower()
            systems_data = collected_state.get('systems', {})
            target_sys_data = systems_data.get(target_sys_key, {})

            actual_val = target_sys_data.get('access_status') or target_sys_data.get('status') or 'UNKNOWN'
            expected_val = rule.expected_value

            # Compare actual vs expected
            if rule.evaluates_drift(employee_status, actual_val):
                # Audit event: Rule evaluated (drift detected)
                AuditLogger.log_event(
                    event_type=AuditEventType.RULE_EVALUATED,
                    actor='ReconciliationEngine',
                    employee=employee_obj,
                    system=rule.target_system,
                    action='EVALUATE_RULE',
                    previous_state=actual_val,
                    new_state=expected_val,
                    result='DRIFT_DETECTED',
                    correlation_id=correlation_id,
                    additional_metadata={
                        'rule_code': rule.rule_code,
                        'rule_name': rule.name,
                        'employee_status': employee_status,
                        'actual_state': actual_val,
                        'expected_state': expected_val,
                    }
                )

                # Drift detected! (e.g. TERMINATED in HR vs ENABLED in VPN)
                violation, created = IntegrityViolation.objects.get_or_create(
                    employee=employee_obj,
                    rule=rule,
                    affected_system=rule.target_system,
                    status=ViolationStatus.OPEN,
                    defaults={
                        'expected_state': expected_val,
                        'actual_state': actual_val,
                        'severity': rule.severity,
                    }
                )

                if not created:
                    # Idempotent update of existing OPEN violation if values changed
                    if violation.actual_state != actual_val or violation.expected_state != expected_val or violation.severity != rule.severity:
                        violation.actual_state = actual_val
                        violation.expected_state = expected_val
                        violation.severity = rule.severity
                        violation.save(update_fields=['actual_state', 'expected_state', 'severity', 'updated_at'])

                # Audit event: Violation detected
                AuditLogger.log_event(
                    event_type=AuditEventType.VIOLATION_DETECTED,
                    actor='ReconciliationEngine',
                    employee=employee_obj,
                    system=rule.target_system,
                    action='DETECT_VIOLATION',
                    previous_state=actual_val,
                    new_state=expected_val,
                    result='VIOLATION_DETECTED',
                    correlation_id=correlation_id,
                    additional_metadata={
                        'violation_id': str(violation.id),
                        'rule_code': rule.rule_code,
                        'severity': rule.severity,
                        'is_new': created
                    }
                )

                detected_violations.append(violation)
            else:
                # Compliant state (e.g. TERMINATED in HR and DISABLED in VPN)
                AuditLogger.log_event(
                    event_type=AuditEventType.RULE_EVALUATED,
                    actor='ReconciliationEngine',
                    employee=employee_obj,
                    system=rule.target_system,
                    action='EVALUATE_RULE',
                    previous_state=actual_val,
                    new_state=expected_val,
                    result='COMPLIANT',
                    correlation_id=correlation_id,
                    additional_metadata={
                        'rule_code': rule.rule_code,
                        'rule_name': rule.name,
                        'employee_status': employee_status,
                        'actual_state': actual_val,
                        'expected_state': expected_val,
                    }
                )

                # Resolve any prior OPEN violation
                open_viols = IntegrityViolation.objects.filter(
                    employee=employee_obj,
                    rule=rule,
                    affected_system=rule.target_system,
                    status=ViolationStatus.OPEN
                )
                for v in open_viols:
                    v.status = ViolationStatus.RESOLVED
                    v.save(update_fields=['status', 'updated_at'])
                    resolved_violations.append(v)

                    # Audit event: Violation resolved
                    AuditLogger.log_event(
                        event_type=AuditEventType.VIOLATION_RESOLVED,
                        actor='ReconciliationEngine',
                        employee=employee_obj,
                        system=rule.target_system,
                        action='RESOLVE_VIOLATION',
                        previous_state=ViolationStatus.OPEN,
                        new_state=ViolationStatus.RESOLVED,
                        result='VIOLATION_RESOLVED',
                        correlation_id=correlation_id,
                        additional_metadata={
                            'violation_id': str(v.id),
                            'rule_code': rule.rule_code,
                            'reason': 'Employee compliant state achieved'
                        }
                    )

        return {
            "employee_id": employee_id,
            "employee_name": collected_state['employee_name'],
            "employee_email": collected_state['employee_email'],
            "employee_status": employee_status,
            "evaluated_at": timezone.now().isoformat(),
            "rules_evaluated_count": active_rules.count(),
            "violations_detected_count": len(detected_violations),
            "violations_resolved_count": len(resolved_violations),
            "correlation_id": correlation_id,
            "violations": [
                {
                    "id": str(v.id),
                    "rule_code": v.rule.rule_code,
                    "rule_name": v.rule.name,
                    "affected_system": v.affected_system,
                    "expected_state": v.expected_state,
                    "actual_state": v.actual_state,
                    "severity": v.severity,
                    "status": v.status,
                    "detected_at": v.detected_at.isoformat()
                } for v in detected_violations
            ]
        }

    def evaluate_all(self) -> list:
        """
        Runs reconciliation engine evaluation across all employees in HR system.
        Returns list of evaluation reports.
        """
        employees = Employee.objects.all().order_by('full_name')
        reports = []
        correlation_id = str(uuid.uuid4())
        for emp in employees:
            reports.append(self.evaluate_employee_rules(emp, correlation_id=correlation_id))
        return reports
