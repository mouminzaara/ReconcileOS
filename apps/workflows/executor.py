"""
Repair Execution Engine for ReconcileOS.

Safely executes approved repair plans against target downstream connectors,
updating target system state, recording attempt logs, handling transient failures with bounded retries,
and invoking post-repair empirical verification.
"""

import logging
import uuid
from typing import Optional
from django.utils import timezone
from apps.approvals.models import ApprovalRequest, ApprovalDecision
from apps.connectors.adapters import ConnectorRegistry, ConnectorException
from apps.reconciliation.collectors import StateCollector
from apps.audit.services import AuditLogger
from apps.audit.models import AuditEventType
from .models import RepairPlan, PlanStatus, RepairExecutionLog, ExecutionStatus

logger = logging.getLogger(__name__)

# Maximum default bounded retries allowed for a failing operation
DEFAULT_MAX_RETRIES = 3


class IneligiblePlanExecutionException(Exception):
    """Raised when an unapproved, rejected, completed, or invalid repair plan is submitted for execution."""
    pass


class ExecutionException(Exception):
    """Raised when repair plan execution fails permanently or exceeds maximum retry attempts."""
    pass


class RepairExecutor:
    """
    Fault-Tolerant, Idempotent Repair Execution Engine.

    Loads approved repair plans, validates eligibility, computes deterministic idempotency keys,
    queries pre-execution target state, executes actions via connector abstraction, logs attempt history,
    handles transient failures via controlled bounded retries, and invokes post-repair verification upon success.
    """

    def __init__(self, state_collector=None):
        self.state_collector = state_collector or StateCollector()

    def verify_plan_eligibility(self, repair_plan: RepairPlan, max_retries: int = DEFAULT_MAX_RETRIES):
        """
        Validates that a RepairPlan is eligible for execution.

        Requirements:
        1. RepairPlan status must NOT be COMPLETED or SUCCESS (idempotency check: prevents redundant execution).
        2. RepairPlan status must be APPROVED, FAILED, or RETRYING.
        3. Must have an associated ApprovalRequest with decision == APPROVED.
        """
        if not repair_plan:
            raise IneligiblePlanExecutionException("Repair plan instance cannot be None.")

        # Idempotency check: prevent re-executing already completed/successful operations
        if repair_plan.status in [PlanStatus.COMPLETED, PlanStatus.SUCCESS]:
            raise IneligiblePlanExecutionException(
                f"Cannot execute repair plan '{repair_plan.id}': Operation is already '{repair_plan.status}'. "
                f"Redundant execution of successful operations is prevented."
            )

        valid_statuses = [PlanStatus.APPROVED, PlanStatus.FAILED, PlanStatus.RETRYING]
        if repair_plan.status not in valid_statuses:
            raise IneligiblePlanExecutionException(
                f"Cannot execute repair plan '{repair_plan.id}': Current status is '{repair_plan.status}'. "
                f"Only APPROVED, FAILED, or RETRYING repair plans are eligible for execution."
            )

        # Check approval request status
        approval_request = ApprovalRequest.objects.filter(repair_plan=repair_plan).order_by('-created_at').first()
        if not approval_request or approval_request.decision != ApprovalDecision.APPROVED:
            raise IneligiblePlanExecutionException(
                f"Cannot execute repair plan '{repair_plan.id}': Approval request requirement not satisfied. "
                f"Status: '{approval_request.decision if approval_request else 'MISSING'}'."
            )

        # Check max attempts limit
        existing_attempts = RepairExecutionLog.objects.filter(repair_plan=repair_plan).count()
        if existing_attempts >= max_retries:
            raise IneligiblePlanExecutionException(
                f"Cannot execute repair plan '{repair_plan.id}': Reached maximum retry limit of {max_retries} attempts."
            )

    def execute_plan(self, repair_plan: RepairPlan, executed_by=None, max_retries: int = DEFAULT_MAX_RETRIES, auto_retry: bool = True, correlation_id: Optional[str] = None) -> RepairExecutionLog:
        """
        Executes an approved RepairPlan with fault-tolerant bounded retry policy and pre-execution idempotency checks.

        Returns:
            RepairExecutionLog: Log object containing execution attempt details and output.
        """
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        actor = str(executed_by.username if hasattr(executed_by, 'username') else executed_by or 'RepairExecutor')

        # 1. Verify plan eligibility & idempotency
        self.verify_plan_eligibility(repair_plan, max_retries=max_retries)

        # 2. Determine current attempt number & deterministic idempotency key
        existing_attempts = RepairExecutionLog.objects.filter(repair_plan=repair_plan).count()
        attempt_number = existing_attempts + 1
        idempotency_key = f"idemp_{repair_plan.id}_attempt_{attempt_number}"

        # 3. Pre-execution state inspection (Timeout-recovery & Idempotency Check)
        target_sys_key = (repair_plan.target_system or '').strip().lower()
        expected_state = str(repair_plan.violation.expected_state or '').strip().upper()

        collected_state = self.state_collector.collect_employee_state(repair_plan.employee)
        target_data = collected_state.get('systems', {}).get(target_sys_key, {})
        actual_state = str(target_data.get('access_status') or target_data.get('status') or 'UNKNOWN').strip().upper()

        now = timezone.now()

        # If pre-execution state ALREADY satisfies expected state (e.g. after a previous attempt timed out after downstream mutation)
        if actual_state == expected_state:
            repair_plan.status = PlanStatus.SUCCESS
            repair_plan.save(update_fields=['status', 'updated_at'])

            msg = (
                f"Pre-execution state inspection: Downstream system '{repair_plan.target_system}' state is already '{actual_state}'. "
                f"Repair action '{repair_plan.action}' idempotently satisfied without duplicate mutation."
            )

            execution_log = RepairExecutionLog.objects.create(
                repair_plan=repair_plan,
                executed_by=executed_by,
                attempt_number=attempt_number,
                idempotency_key=idempotency_key,
                status=ExecutionStatus.SUCCESS,
                already_satisfied=True,
                output_message=msg,
                completed_at=now
            )

            AuditLogger.log_event(
                event_type=AuditEventType.REPAIR_EXECUTED,
                actor=actor,
                employee=repair_plan.employee,
                system=repair_plan.target_system,
                action=repair_plan.action,
                previous_state=actual_state,
                new_state=expected_state,
                result='ALREADY_SATISFIED',
                correlation_id=correlation_id,
                additional_metadata={
                    'plan_id': str(repair_plan.id),
                    'attempt_number': attempt_number,
                    'already_satisfied': True
                }
            )

            # Trigger Post-Repair Empirical Verification
            from .verifier import PostRepairVerifier
            verifier = PostRepairVerifier(state_collector=self.state_collector)
            verifier.verify_repair(repair_plan, correlation_id=correlation_id)

            logger.info(f"Pre-check idempotency satisfied for plan {repair_plan.id} on attempt #{attempt_number}.")
            return execution_log

        # 4. Update plan status to EXECUTING
        repair_plan.status = PlanStatus.EXECUTING
        repair_plan.save(update_fields=['status', 'updated_at'])

        # 5. Record attempt log entry
        execution_log = RepairExecutionLog.objects.create(
            repair_plan=repair_plan,
            executed_by=executed_by,
            attempt_number=attempt_number,
            idempotency_key=idempotency_key,
            status=ExecutionStatus.EXECUTING,
            output_message=f"Attempt #{attempt_number}: Executing action '{repair_plan.action}' on system '{repair_plan.target_system}'..."
        )

        logger.info(f"Started execution attempt #{attempt_number} (Key: {idempotency_key}) for repair plan {repair_plan.id}.")

        # 6. Execute action via target connector abstraction
        try:
            connector = ConnectorRegistry.get_connector(repair_plan.target_system)
            result = connector.execute_action(
                employee=repair_plan.employee,
                action=repair_plan.action
            )

            completed_now = timezone.now()
            if result.get('success', False):
                # Successful execution
                output_msg = result.get('message', 'Action executed successfully by connector.')
                is_already_satisfied = result.get('details', {}).get('already_satisfied', False)

                execution_log.status = ExecutionStatus.SUCCESS
                execution_log.already_satisfied = is_already_satisfied
                execution_log.output_message = output_msg
                execution_log.completed_at = completed_now
                execution_log.save(update_fields=['status', 'already_satisfied', 'output_message', 'completed_at'])

                repair_plan.status = PlanStatus.SUCCESS
                repair_plan.save(update_fields=['status', 'updated_at'])

                AuditLogger.log_event(
                    event_type=AuditEventType.REPAIR_EXECUTED,
                    actor=actor,
                    employee=repair_plan.employee,
                    system=repair_plan.target_system,
                    action=repair_plan.action,
                    previous_state=actual_state,
                    new_state=expected_state,
                    result='SUCCESS',
                    correlation_id=correlation_id,
                    additional_metadata={
                        'plan_id': str(repair_plan.id),
                        'attempt_number': attempt_number,
                        'output_message': output_msg
                    }
                )

                # Automatically trigger Post-Repair Empirical Verification
                from .verifier import PostRepairVerifier
                verifier = PostRepairVerifier(state_collector=self.state_collector)
                verifier.verify_repair(repair_plan, correlation_id=correlation_id)

                logger.info(f"Attempt #{attempt_number} SUCCESS for plan {repair_plan.id}.")
                return execution_log

            else:
                # Connector reported failure
                error_msg = result.get('message', 'Connector reported execution failure.')
                execution_log.status = ExecutionStatus.FAILED
                execution_log.error_details = error_msg
                execution_log.completed_at = completed_now
                execution_log.save(update_fields=['status', 'error_details', 'completed_at'])

                logger.warning(f"Attempt #{attempt_number} FAILED for plan {repair_plan.id}: {error_msg}")

                AuditLogger.log_event(
                    event_type=AuditEventType.EXECUTION_FAILED,
                    actor=actor,
                    employee=repair_plan.employee,
                    system=repair_plan.target_system,
                    action=repair_plan.action,
                    previous_state=actual_state,
                    new_state=expected_state,
                    result='FAILED',
                    correlation_id=correlation_id,
                    additional_metadata={
                        'plan_id': str(repair_plan.id),
                        'attempt_number': attempt_number,
                        'error_details': error_msg
                    }
                )

                # Check if bounded retry policy should trigger auto-retry
                if auto_retry and attempt_number < max_retries:
                    repair_plan.status = PlanStatus.RETRYING
                    repair_plan.save(update_fields=['status', 'updated_at'])

                    AuditLogger.log_event(
                        event_type=AuditEventType.RETRY_PERFORMED,
                        actor=actor,
                        employee=repair_plan.employee,
                        system=repair_plan.target_system,
                        action=repair_plan.action,
                        previous_state=PlanStatus.FAILED,
                        new_state=PlanStatus.RETRYING,
                        result='RETRYING',
                        correlation_id=correlation_id,
                        additional_metadata={
                            'plan_id': str(repair_plan.id),
                            'failed_attempt': attempt_number,
                            'next_attempt': attempt_number + 1,
                            'max_retries': max_retries
                        }
                    )

                    logger.info(f"Triggering auto-retry (Attempt #{attempt_number + 1} of {max_retries}) for plan {repair_plan.id}...")
                    return self.execute_plan(repair_plan, executed_by=executed_by, max_retries=max_retries, auto_retry=auto_retry, correlation_id=correlation_id)
                else:
                    repair_plan.status = PlanStatus.FAILED
                    repair_plan.save(update_fields=['status', 'updated_at'])
                    return execution_log

        except ConnectorException as exc:
            completed_now = timezone.now()
            execution_log.status = ExecutionStatus.FAILED
            execution_log.error_details = str(exc)
            execution_log.completed_at = completed_now
            execution_log.save(update_fields=['status', 'error_details', 'completed_at'])

            logger.error(f"Attempt #{attempt_number} connector exception for plan {repair_plan.id}: {exc}")

            AuditLogger.log_event(
                event_type=AuditEventType.EXECUTION_FAILED,
                actor=actor,
                employee=repair_plan.employee,
                system=repair_plan.target_system,
                action=repair_plan.action,
                previous_state=actual_state,
                new_state=expected_state,
                result='FAILED_CONNECTOR_EXCEPTION',
                correlation_id=correlation_id,
                additional_metadata={
                    'plan_id': str(repair_plan.id),
                    'attempt_number': attempt_number,
                    'error_details': str(exc)
                }
            )

            if auto_retry and attempt_number < max_retries:
                repair_plan.status = PlanStatus.RETRYING
                repair_plan.save(update_fields=['status', 'updated_at'])

                AuditLogger.log_event(
                    event_type=AuditEventType.RETRY_PERFORMED,
                    actor=actor,
                    employee=repair_plan.employee,
                    system=repair_plan.target_system,
                    action=repair_plan.action,
                    previous_state=PlanStatus.FAILED,
                    new_state=PlanStatus.RETRYING,
                    result='RETRYING',
                    correlation_id=correlation_id,
                    additional_metadata={
                        'plan_id': str(repair_plan.id),
                        'failed_attempt': attempt_number,
                        'next_attempt': attempt_number + 1,
                        'max_retries': max_retries
                    }
                )

                logger.info(f"Triggering auto-retry (Attempt #{attempt_number + 1} of {max_retries}) for plan {repair_plan.id}...")
                return self.execute_plan(repair_plan, executed_by=executed_by, max_retries=max_retries, auto_retry=auto_retry, correlation_id=correlation_id)
            else:
                repair_plan.status = PlanStatus.FAILED
                repair_plan.save(update_fields=['status', 'updated_at'])
                raise ExecutionException(f"Connector error after attempt #{attempt_number}: {exc}") from exc

        except Exception as exc:
            completed_now = timezone.now()
            execution_log.status = ExecutionStatus.FAILED
            execution_log.error_details = f"Unexpected execution failure: {exc}"
            execution_log.completed_at = completed_now
            execution_log.save(update_fields=['status', 'error_details', 'completed_at'])

            repair_plan.status = PlanStatus.FAILED
            repair_plan.save(update_fields=['status', 'updated_at'])

            logger.error(f"Unexpected error on attempt #{attempt_number} for plan {repair_plan.id}: {exc}")

            AuditLogger.log_event(
                event_type=AuditEventType.EXECUTION_FAILED,
                actor=actor,
                employee=repair_plan.employee,
                system=repair_plan.target_system,
                action=repair_plan.action,
                previous_state=actual_state,
                new_state=expected_state,
                result='FAILED_UNEXPECTED_EXCEPTION',
                correlation_id=correlation_id,
                additional_metadata={
                    'plan_id': str(repair_plan.id),
                    'attempt_number': attempt_number,
                    'error_details': str(exc)
                }
            )

            raise ExecutionException(f"Unexpected error: {exc}") from exc
