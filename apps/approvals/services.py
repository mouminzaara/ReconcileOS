"""
Service logic for ReconcileOS Human-in-the-Loop Approvals Engine.
"""

import logging
import uuid
from typing import Optional
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.workflows.models import RepairPlan, PlanStatus
from apps.audit.services import AuditLogger
from apps.audit.models import AuditEventType
from .models import ApprovalRequest, ApprovalDecision

logger = logging.getLogger(__name__)


class ApprovalService:
    """
    Service class orchestrating Approval Request lifecycles and state transitions.
    """

    @staticmethod
    def create_approval_request(repair_plan: RepairPlan, requested_by=None, correlation_id: Optional[str] = None) -> ApprovalRequest:
        """
        Creates a new PENDING approval request for a RepairPlan if one does not already exist.
        """
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        existing = ApprovalRequest.objects.filter(
            repair_plan=repair_plan,
            decision=ApprovalDecision.PENDING
        ).first()

        if existing:
            return existing

        request = ApprovalRequest.objects.create(
            repair_plan=repair_plan,
            requested_by=requested_by,
            decision=ApprovalDecision.PENDING
        )

        actor = str(requested_by.username if hasattr(requested_by, 'username') else requested_by or 'SYSTEM')

        AuditLogger.log_event(
            event_type=AuditEventType.APPROVAL_REQUESTED,
            actor=actor,
            employee=repair_plan.employee,
            system=repair_plan.target_system,
            action='REQUEST_APPROVAL',
            previous_state=PlanStatus.PENDING,
            new_state=ApprovalDecision.PENDING,
            result='APPROVAL_REQUESTED',
            correlation_id=correlation_id,
            additional_metadata={
                'approval_request_id': str(request.id),
                'plan_id': str(repair_plan.id),
                'risk_level': repair_plan.risk_level
            }
        )

        logger.info(f"Created PENDING approval request {request.id} for repair plan {repair_plan.id}.")
        return request

    @staticmethod
    def approve_request(approval_request: ApprovalRequest, decided_by=None, comment: str = '', correlation_id: Optional[str] = None) -> ApprovalRequest:
        """
        Approves a PENDING approval request and synchronizes the associated RepairPlan status to APPROVED.

        Raises ValidationError if invalid transition is attempted.
        """
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        if approval_request.decision != ApprovalDecision.PENDING:
            raise ValidationError(
                f"Cannot approve request {approval_request.id}: Current decision status is '{approval_request.decision}'. "
                f"Only PENDING approval requests can be approved."
            )

        repair_plan = approval_request.repair_plan
        if repair_plan.status not in [PlanStatus.PENDING]:
            raise ValidationError(
                f"Cannot approve repair plan {repair_plan.id}: Plan status is '{repair_plan.status}'. "
                f"Only PENDING repair plans can be approved."
            )

        now = timezone.now()

        # Update ApprovalRequest
        approval_request.decision = ApprovalDecision.APPROVED
        approval_request.decided_by = decided_by
        approval_request.decided_at = now
        if comment:
            approval_request.comment = comment
        approval_request.save(update_fields=['decision', 'decided_by', 'decided_at', 'comment', 'updated_at'])

        # Update associated RepairPlan status -> APPROVED (Eligible for execution, but NOT executed yet)
        repair_plan.status = PlanStatus.APPROVED
        repair_plan.save(update_fields=['status', 'updated_at'])

        actor = str(decided_by.username if hasattr(decided_by, 'username') else decided_by or 'SYSTEM')

        AuditLogger.log_event(
            event_type=AuditEventType.REPAIR_APPROVED,
            actor=actor,
            employee=repair_plan.employee,
            system=repair_plan.target_system,
            action='APPROVE_REPAIR',
            previous_state=PlanStatus.PENDING,
            new_state=PlanStatus.APPROVED,
            result='REPAIR_APPROVED',
            correlation_id=correlation_id,
            additional_metadata={
                'approval_request_id': str(approval_request.id),
                'plan_id': str(repair_plan.id),
                'comment': comment
            }
        )

        logger.info(
            f"Approved request {approval_request.id} for plan {repair_plan.id}. "
            f"Plan status updated to APPROVED (eligible for execution)."
        )
        return approval_request

    @staticmethod
    def reject_request(approval_request: ApprovalRequest, decided_by=None, comment: str = '', correlation_id: Optional[str] = None) -> ApprovalRequest:
        """
        Rejects a PENDING approval request and synchronizes the associated RepairPlan status to REJECTED.

        Raises ValidationError if invalid transition is attempted.
        """
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        if approval_request.decision != ApprovalDecision.PENDING:
            raise ValidationError(
                f"Cannot reject request {approval_request.id}: Current decision status is '{approval_request.decision}'. "
                f"Only PENDING approval requests can be rejected."
            )

        repair_plan = approval_request.repair_plan
        if repair_plan.status not in [PlanStatus.PENDING]:
            raise ValidationError(
                f"Cannot reject repair plan {repair_plan.id}: Plan status is '{repair_plan.status}'. "
                f"Only PENDING repair plans can be rejected."
            )

        now = timezone.now()

        # Update ApprovalRequest
        approval_request.decision = ApprovalDecision.REJECTED
        approval_request.decided_by = decided_by
        approval_request.decided_at = now
        if comment:
            approval_request.comment = comment
        approval_request.save(update_fields=['decision', 'decided_by', 'decided_at', 'comment', 'updated_at'])

        # Update associated RepairPlan status -> REJECTED
        repair_plan.status = PlanStatus.REJECTED
        repair_plan.save(update_fields=['status', 'updated_at'])

        actor = str(decided_by.username if hasattr(decided_by, 'username') else decided_by or 'SYSTEM')

        AuditLogger.log_event(
            event_type=AuditEventType.REPAIR_REJECTED,
            actor=actor,
            employee=repair_plan.employee,
            system=repair_plan.target_system,
            action='REJECT_REPAIR',
            previous_state=PlanStatus.PENDING,
            new_state=PlanStatus.REJECTED,
            result='REPAIR_REJECTED',
            correlation_id=correlation_id,
            additional_metadata={
                'approval_request_id': str(approval_request.id),
                'plan_id': str(repair_plan.id),
                'comment': comment
            }
        )

        logger.info(f"Rejected request {approval_request.id} for plan {repair_plan.id}. Plan status updated to REJECTED.")
        return approval_request
