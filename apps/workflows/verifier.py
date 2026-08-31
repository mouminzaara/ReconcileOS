"""
Post-Repair Verification Engine for ReconcileOS.

Re-queries target downstream system state empirically to verify that
remediation achieved expected state compliance before marking plans COMPLETED
and resolving integrity violations.
"""

import logging
import uuid
from typing import Optional
from django.utils import timezone
from apps.reconciliation.collectors import StateCollector
from apps.reconciliation.models import ViolationStatus
from apps.audit.services import AuditLogger
from apps.audit.models import AuditEventType
from .models import RepairPlan, PlanStatus, RepairVerification, VerificationResult

logger = logging.getLogger(__name__)


class PostRepairVerifier:
    """
    Post-Repair Verification Engine.

    Empirically checks downstream target system state after repair execution.
    """

    def __init__(self, state_collector=None):
        self.state_collector = state_collector or StateCollector()

    def verify_repair(self, repair_plan: RepairPlan, correlation_id: Optional[str] = None) -> RepairVerification:
        """
        Re-queries the target system for repair_plan.employee, compares actual vs expected state,
        records RepairVerification, and updates RepairPlan and IntegrityViolation statuses accordingly.

        Returns:
            RepairVerification: Model instance containing empirical check outcome.
        """
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        expected_state = repair_plan.violation.expected_state
        target_sys_key = (repair_plan.target_system or '').strip().lower()

        # 1. Collect fresh multi-system state from downstream system
        collected_state = self.state_collector.collect_employee_state(repair_plan.employee)
        systems_data = collected_state.get('systems', {})
        target_data = systems_data.get(target_sys_key, {})

        actual_state = (
            target_data.get('access_status') or
            target_data.get('status') or
            'UNKNOWN'
        )

        now = timezone.now()

        # 2. Compare actual vs expected state
        expected_upper = str(expected_state or '').strip().upper()
        actual_upper = str(actual_state or '').strip().upper()

        if actual_upper == expected_upper:
            # Verification VERIFIED (State Consistent!)
            verification = RepairVerification.objects.create(
                repair_plan=repair_plan,
                expected_state=expected_state,
                actual_state=actual_state,
                result=VerificationResult.VERIFIED,
                verified_at=now,
                details=(
                    f"Post-repair verification SUCCESS: Downstream system '{repair_plan.target_system}' "
                    f"state is '{actual_state}', matching expected state '{expected_state}'."
                )
            )

            # Update RepairPlan status -> COMPLETED
            repair_plan.status = PlanStatus.COMPLETED
            repair_plan.save(update_fields=['status', 'updated_at'])

            # Update IntegrityViolation status -> RESOLVED
            violation = repair_plan.violation
            violation.status = ViolationStatus.RESOLVED
            violation.save(update_fields=['status', 'updated_at'])

            AuditLogger.log_event(
                event_type=AuditEventType.VERIFICATION_PERFORMED,
                actor='PostRepairVerifier',
                employee=repair_plan.employee,
                system=repair_plan.target_system,
                action='VERIFY_REPAIR',
                previous_state=actual_state,
                new_state=expected_state,
                result='VERIFIED',
                correlation_id=correlation_id,
                additional_metadata={
                    'plan_id': str(repair_plan.id),
                    'verification_id': str(verification.id),
                    'violation_id': str(violation.id)
                }
            )

            AuditLogger.log_event(
                event_type=AuditEventType.VIOLATION_RESOLVED,
                actor='PostRepairVerifier',
                employee=repair_plan.employee,
                system=repair_plan.target_system,
                action='RESOLVE_VIOLATION',
                previous_state=ViolationStatus.OPEN,
                new_state=ViolationStatus.RESOLVED,
                result='VIOLATION_RESOLVED',
                correlation_id=correlation_id,
                additional_metadata={
                    'plan_id': str(repair_plan.id),
                    'violation_id': str(violation.id),
                    'reason': 'Post-repair verification succeeded'
                }
            )

            logger.info(
                f"Post-repair verification VERIFIED for plan {repair_plan.id}. "
                f"Violation {violation.id} resolved."
            )
            return verification

        else:
            # Verification VERIFICATION_FAILED (Inconsistent state detected!)
            verification = RepairVerification.objects.create(
                repair_plan=repair_plan,
                expected_state=expected_state,
                actual_state=actual_state,
                result=VerificationResult.VERIFICATION_FAILED,
                verified_at=now,
                details=(
                    f"Post-repair verification FAILED: Downstream system '{repair_plan.target_system}' "
                    f"state is '{actual_state}', but expected state was '{expected_state}'."
                )
            )

            # Update RepairPlan status -> FAILED
            repair_plan.status = PlanStatus.FAILED
            repair_plan.save(update_fields=['status', 'updated_at'])

            AuditLogger.log_event(
                event_type=AuditEventType.VERIFICATION_FAILED,
                actor='PostRepairVerifier',
                employee=repair_plan.employee,
                system=repair_plan.target_system,
                action='VERIFY_REPAIR',
                previous_state=actual_state,
                new_state=expected_state,
                result='VERIFICATION_FAILED',
                correlation_id=correlation_id,
                additional_metadata={
                    'plan_id': str(repair_plan.id),
                    'verification_id': str(verification.id),
                    'violation_id': str(repair_plan.violation.id)
                }
            )

            # IntegrityViolation remains OPEN
            logger.warning(
                f"Post-repair verification FAILED for plan {repair_plan.id}. "
                f"Expected '{expected_state}', found '{actual_state}'. Violation remains OPEN."
            )
            return verification
