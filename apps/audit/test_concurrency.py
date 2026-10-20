"""
Concurrency and Tamper-Evidence Integrity Test Suite for Audit Logging System (Phase 2B).

Verifies that concurrent writes across multiple threads produce a strictly valid,
sequential SHA-256 cryptographic hash chain without forks or broken links,
and validates that tampering, missing records, or altered hashes are reliably detected.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from django.test import TransactionTestCase
from django.core.exceptions import ValidationError

from apps.employees.models import Employee, EmployeeStatus
from apps.audit.models import AuditLog, AuditEventType
from apps.audit.services import AuditLogger


class AuditConcurrencyAndIntegrityTestCase(TransactionTestCase):
    """
    Test suite for genuine concurrent audit logging and cryptographic integrity verification.
    """

    def setUp(self):
        self.employee = Employee.objects.create(
            full_name="Audit Concurrency Subject",
            email="audit_concur@example.com",
            department="Security",
            status=EmployeeStatus.ACTIVE
        )

    def test_concurrent_audit_writes_preserve_valid_hash_chain(self):
        """
        Submits 30 concurrent audit log entries across 8 worker threads simultaneously.
        Verifies that:
        1. All 30 entries are persisted.
        2. Every single entry correctly references the hash of its predecessor.
        3. No forked records or duplicate previous_hash values exist.
        4. AuditLogger.verify_chain_integrity() confirms 100% cryptographic validity.
        """
        initial_records_count = AuditLog.objects.count()
        num_entries = 30
        max_workers = 8

        def write_audit_log(index):
            return AuditLogger.log_event(
                event_type=AuditEventType.RULE_EVALUATED,
                actor=f"WorkerThread-{index}",
                employee=self.employee,
                system="VPN",
                action="CONCURRENT_RULE_EVALUATION",
                previous_state="ENABLED",
                new_state="ENABLED",
                result="COMPLIANT",
                additional_metadata={"index": index}
            )

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = [pool.submit(write_audit_log, i) for i in range(num_entries)]
            created_entries = [f.result() for f in as_completed(futures)]

        self.assertEqual(len(created_entries), num_entries)
        total_records = AuditLog.objects.count()
        self.assertEqual(total_records, initial_records_count + num_entries)

        # Verify cryptographic chain integrity across all records
        is_valid, message, details = AuditLogger.verify_chain_integrity(
            expected_count=total_records
        )
        self.assertTrue(is_valid, f"Chain integrity failed: {message} | Details: {details}")
        self.assertEqual(details["total_records"], total_records)
        self.assertEqual(details["verified_records"], total_records)

        # Inspect sequential linkage manually as double-check
        records = list(AuditLog.objects.order_by('timestamp', 'id'))
        for i in range(1, len(records)):
            prev_record = records[i - 1]
            curr_record = records[i]
            self.assertEqual(
                curr_record.previous_hash,
                prev_record.current_hash,
                f"Linkage broken at index {i}: curr.previous_hash != prev.current_hash"
            )
            self.assertEqual(
                curr_record.current_hash,
                curr_record.calculate_payload_hash(curr_record.previous_hash),
                f"Payload hash altered at index {i}"
            )

    def test_verification_detects_deliberately_corrupted_payload(self):
        """
        Verify that tampering with an audit record's payload (bypassing model save)
        is immediately detected by verify_chain_integrity with CURRENT_HASH_MISMATCH.
        """
        log1 = AuditLogger.log_event(event_type=AuditEventType.RULE_EVALUATED, actor="Engine")
        log2 = AuditLogger.log_event(event_type=AuditEventType.VIOLATION_DETECTED, actor="Engine")
        log3 = AuditLogger.log_event(event_type=AuditEventType.REPAIR_PLAN_CREATED, actor="Planner")

        # Verify intact before tampering
        is_valid, _, _ = AuditLogger.verify_chain_integrity()
        self.assertTrue(is_valid)

        # Directly tamper via SQL update
        AuditLog.objects.filter(pk=log2.pk).update(result="TAMPERED_RESULT")

        # Must detect payload tamper
        is_valid, msg, details = AuditLogger.verify_chain_integrity()
        self.assertFalse(is_valid)
        self.assertIn("stored current_hash", msg)
        self.assertEqual(details["reason"], "CURRENT_HASH_MISMATCH")
        self.assertEqual(details["tampered_record_id"], str(log2.id))

    def test_verification_detects_broken_link_or_missing_record(self):
        """
        Verify that a record whose previous_hash is corrupted or does not match
        the expected preceding hash is detected with PREVIOUS_HASH_MISMATCH.
        """
        log1 = AuditLogger.log_event(event_type=AuditEventType.RULE_EVALUATED, actor="Engine")
        log2 = AuditLogger.log_event(event_type=AuditEventType.VIOLATION_DETECTED, actor="Engine")

        # Directly tamper previous_hash of log2
        AuditLog.objects.filter(pk=log2.pk).update(previous_hash="f" * 64)

        is_valid, msg, details = AuditLogger.verify_chain_integrity()
        self.assertFalse(is_valid)
        self.assertIn("previous_hash", msg)
        self.assertEqual(details["reason"], "PREVIOUS_HASH_MISMATCH")
        self.assertEqual(details["tampered_record_id"], str(log2.id))

    def test_verification_detects_head_hash_and_count_mismatches(self):
        """
        Verify that if expected_count or expected_head_hash is provided,
        truncation or count mismatches are caught.
        """
        log1 = AuditLogger.log_event(event_type=AuditEventType.RULE_EVALUATED, actor="Engine")
        log2 = AuditLogger.log_event(event_type=AuditEventType.VIOLATION_DETECTED, actor="Engine")

        # 1. Count mismatch
        is_valid, msg, details = AuditLogger.verify_chain_integrity(expected_count=999)
        self.assertFalse(is_valid)
        self.assertEqual(details["reason"], "RECORD_COUNT_MISMATCH")

        # 2. Head hash mismatch
        is_valid, msg, details = AuditLogger.verify_chain_integrity(expected_head_hash="0" * 64)
        self.assertFalse(is_valid)
        self.assertEqual(details["reason"], "HEAD_HASH_MISMATCH")

    def test_append_only_model_constraints(self):
        """
        Verify that calling .save() on an existing record or .delete() raises ValidationError.
        """
        log = AuditLogger.log_event(event_type=AuditEventType.RULE_EVALUATED, actor="Engine")

        log.actor = "MaliciousUser"
        with self.assertRaises(ValidationError) as ctx:
            log.save()
        self.assertIn("append-only and cannot be updated", str(ctx.exception))

        with self.assertRaises(ValidationError) as ctx:
            log.delete()
        self.assertIn("append-only and cannot be deleted", str(ctx.exception))
