"""
Repair Planning Engine for ReconcileOS.

Generates safe, deterministic repair plans for active integrity violations
without mutating target system states or executing repair actions.
"""

import logging
import uuid
from typing import Tuple, List, Optional
from apps.reconciliation.models import IntegrityViolation, ViolationStatus
from apps.audit.services import AuditLogger
from apps.audit.models import AuditEventType
from .models import RepairPlan, PlanStatus

logger = logging.getLogger(__name__)

# Active statuses that indicate an unresolved / ongoing repair plan
ACTIVE_PLAN_STATUSES = [
    PlanStatus.PENDING,
    PlanStatus.APPROVED,
    PlanStatus.EXECUTING,
]


class RepairPlanner:
    """
    Deterministic Repair Planner Service.

    Transforms integrity violations (authorization drifts) into concrete,
    structured repair plans.
    """

    def plan_for_violation(self, violation: IntegrityViolation, correlation_id: Optional[str] = None) -> Tuple[RepairPlan, bool]:
        """
        Generates a repair plan for a single IntegrityViolation.

        Idempotently prevents creating duplicate active repair plans for the same
        unresolved violation.

        Returns:
            Tuple[RepairPlan, bool]: (repair_plan, created_boolean)
        """
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        # 1. Check for existing active repair plan for this violation
        existing_plan = RepairPlan.objects.filter(
            violation=violation,
            status__in=ACTIVE_PLAN_STATUSES
        ).order_by('-created_at').first()

        if existing_plan:
            logger.info(
                f"Active repair plan {existing_plan.id} already exists for violation {violation.id}. "
                f"Skipping duplicate creation."
            )
            return existing_plan, False

        # 2. Derive deterministic action, reason, and risk_level
        action = self.derive_deterministic_action(
            target_system=violation.affected_system,
            expected_state=violation.expected_state,
            actual_state=violation.actual_state
        )

        reason = (
            f"Integrity violation detected (ID: {violation.id}). Employee {violation.employee.full_name} "
            f"status is '{violation.employee.status}', but {violation.affected_system} access is '{violation.actual_state}'. "
            f"Expected state required by rule {violation.rule.rule_code}: '{violation.expected_state}'. "
            f"Repair action required: {action}."
        )

        risk_level = violation.severity

        # 3. Create the RepairPlan in PENDING status (no execution performed)
        plan = RepairPlan.objects.create(
            employee=violation.employee,
            violation=violation,
            target_system=violation.affected_system,
            action=action,
            reason=reason,
            risk_level=risk_level,
            status=PlanStatus.PENDING
        )

        # Audit Event: Repair Plan Created
        AuditLogger.log_event(
            event_type=AuditEventType.REPAIR_PLAN_CREATED,
            actor='RepairPlanner',
            employee=violation.employee,
            system=violation.affected_system,
            action=action,
            previous_state=violation.actual_state,
            new_state=violation.expected_state,
            result='PLAN_CREATED',
            correlation_id=correlation_id,
            additional_metadata={
                'plan_id': str(plan.id),
                'violation_id': str(violation.id),
                'risk_level': risk_level,
                'status': plan.status
            }
        )

        # 4. Automatically create associated PENDING ApprovalRequest
        from apps.approvals.services import ApprovalService
        ApprovalService.create_approval_request(plan, correlation_id=correlation_id)

        logger.info(
            f"Generated new repair plan {plan.id} [{plan.action}] for violation {violation.id}."
        )
        return plan, True

    def derive_deterministic_action(self, target_system: str, expected_state: str, actual_state: str) -> str:
        """
        Deterministically constructs the standardized repair action string given system and expected state.

        Example:
            target_system="VPN", expected_state="DISABLED", actual_state="ENABLED"
            -> "DISABLE VPN ACCESS"
        """
        target_sys_upper = (target_system or '').strip().upper()
        expected_upper = (expected_state or '').strip().upper()

        if target_sys_upper == 'VPN':
            if expected_upper == 'DISABLED':
                return 'DISABLE VPN ACCESS'
            elif expected_upper == 'ENABLED':
                return 'ENABLE VPN ACCESS'

        # Generic deterministic fallback title format
        if expected_upper.endswith('ED'):
            action_verb = expected_upper[:-2] + 'E' if expected_upper.endswith('D') else expected_upper
        else:
            action_verb = expected_upper

        # Clean verb formatting
        if action_verb == 'DISABLE':
            return f"DISABLE {target_sys_upper} ACCESS"
        elif action_verb == 'ENABLE':
            return f"ENABLE {target_sys_upper} ACCESS"

        return f"SET {target_sys_upper} ACCESS TO {expected_upper}"

    def plan_all_open_violations(self, employee_id: Optional[str] = None, correlation_id: Optional[str] = None) -> List[RepairPlan]:
        """
        Scans all OPEN integrity violations (optionally filtered by employee)
        and generates repair plans idempotently.

        Returns:
            List[RepairPlan]: List of active RepairPlan objects.
        """
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        query = IntegrityViolation.objects.filter(status=ViolationStatus.OPEN)
        if employee_id:
            query = query.filter(employee_id=employee_id)

        plans = []
        for violation in query.select_related('employee', 'rule'):
            plan, _ = self.plan_for_violation(violation, correlation_id=correlation_id)
            plans.append(plan)

        return plans
