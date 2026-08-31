"""
Audit Service & Integrity Verification Engine for ReconcileOS.
"""

import logging
import uuid
from typing import Optional, Dict, Any, Tuple
from django.db import transaction
from apps.employees.models import Employee
from .models import AuditLog, AuditEventType

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Centralized Audit Logger Service.

    Emits append-only, tamper-evident audit records and provides chain integrity verification.
    """

    @staticmethod
    def log_event(
        event_type: str,
        actor: str = 'SYSTEM',
        employee: Optional[Employee] = None,
        system: str = '',
        action: str = '',
        previous_state: str = '',
        new_state: str = '',
        result: str = '',
        correlation_id: Optional[str] = None,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """
        Creates and persists a new AuditLog entry atomically.

        Args:
            event_type: One of AuditEventType values.
            actor: User username/email or system component name.
            employee: Employee model instance if applicable.
            system: Affected system/connector name (e.g., 'VPN', 'GitHub').
            action: Action string performed.
            previous_state: State prior to action.
            new_state: State after action.
            result: Outcome result string ('SUCCESS', 'FAILED', 'DRIFT_DETECTED', etc.).
            correlation_id: Unique correlation UUID string linking pipeline events.
            additional_metadata: Dict with extra context details.

        Returns:
            AuditLog: The persisted audit log instance.
        """
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        metadata = additional_metadata or {}

        with transaction.atomic():
            audit_entry = AuditLog(
                event_type=event_type,
                actor=actor,
                employee=employee,
                system=system,
                action=action,
                previous_state=previous_state,
                new_state=new_state,
                result=result,
                correlation_id=str(correlation_id),
                additional_metadata=metadata
            )
            audit_entry.save()

        logger.debug(
            f"Logged audit event {event_type} (Correlation ID: {correlation_id}, Hash: {audit_entry.current_hash[:8]}...)"
        )
        return audit_entry

    @staticmethod
    def verify_chain_integrity() -> Tuple[bool, str, Dict[str, Any]]:
        """
        Verifies the tamper-evident cryptographic SHA-256 hash chain across all AuditLog records.

        Returns:
            Tuple[bool, str, dict]: (is_valid, message, details_dict)
        """
        records = list(AuditLog.objects.order_by('timestamp', 'id'))
        total_count = len(records)

        if total_count == 0:
            return True, "Audit log is empty. Chain is valid.", {"total_records": 0, "verified_records": 0}

        expected_prev_hash = '0' * 64

        for index, record in enumerate(records):
            # 1. Verify previous_hash linkage
            if record.previous_hash != expected_prev_hash:
                err_msg = (
                    f"Tamper detected at record #{index} (ID: {record.id}): "
                    f"previous_hash '{record.previous_hash}' does not match expected '{expected_prev_hash}'."
                )
                logger.error(err_msg)
                return False, err_msg, {
                    "total_records": total_count,
                    "verified_records": index,
                    "tampered_record_id": str(record.id),
                    "reason": "PREVIOUS_HASH_MISMATCH"
                }

            # 2. Recompute current_hash payload digest
            recomputed_hash = record.calculate_payload_hash(record.previous_hash)
            if record.current_hash != recomputed_hash:
                err_msg = (
                    f"Tamper detected at record #{index} (ID: {record.id}): "
                    f"stored current_hash '{record.current_hash}' does not match recomputed '{recomputed_hash}'."
                )
                logger.error(err_msg)
                return False, err_msg, {
                    "total_records": total_count,
                    "verified_records": index,
                    "tampered_record_id": str(record.id),
                    "reason": "CURRENT_HASH_MISMATCH"
                }

            # Advance chain expected link
            expected_prev_hash = record.current_hash

        success_msg = f"Cryptographic chain integrity verified. All {total_count} records intact."
        logger.info(success_msg)
        return True, success_msg, {
            "total_records": total_count,
            "verified_records": total_count,
            "head_hash": expected_prev_hash
        }
