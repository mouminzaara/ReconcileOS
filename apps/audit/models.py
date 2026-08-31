"""
Audit Log Models for ReconcileOS.

Provides an append-only, tamper-evident audit record stream for all critical system
decisions, rule evaluations, violations, repair plans, approvals, executions, retries,
verifications, and resolutions.
"""

import uuid
import hashlib
import json
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.employees.models import Employee


class AuditEventType(models.TextChoices):
    RULE_EVALUATED = 'rule_evaluated', 'Rule Evaluated'
    VIOLATION_DETECTED = 'violation_detected', 'Violation Detected'
    REPAIR_PLAN_CREATED = 'repair_plan_created', 'Repair Plan Created'
    APPROVAL_REQUESTED = 'approval_requested', 'Approval Requested'
    REPAIR_APPROVED = 'repair_approved', 'Repair Approved'
    REPAIR_REJECTED = 'repair_rejected', 'Repair Rejected'
    REPAIR_EXECUTED = 'repair_executed', 'Repair Executed'
    EXECUTION_FAILED = 'execution_failed', 'Execution Failed'
    RETRY_PERFORMED = 'retry_performed', 'Retry Performed'
    VERIFICATION_PERFORMED = 'verification_performed', 'Verification Performed'
    VERIFICATION_FAILED = 'verification_failed', 'Verification Failed'
    VIOLATION_RESOLVED = 'violation_resolved', 'Violation Resolved'


class AuditLog(models.Model):
    """
    Append-Only, Tamper-Evident Audit Log Model.

    Calculates a cryptographic SHA-256 hash over its contents combined with the
    previous record's hash. Prohibits updating or deleting existing records.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True, editable=False)
    actor = models.CharField(max_length=255, default='SYSTEM', db_index=True)
    event_type = models.CharField(max_length=64, choices=AuditEventType.choices, db_index=True)
    employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    system = models.CharField(max_length=64, blank=True, default='', db_index=True)
    action = models.CharField(max_length=255, blank=True, default='')
    previous_state = models.CharField(max_length=128, blank=True, default='')
    new_state = models.CharField(max_length=128, blank=True, default='')
    result = models.CharField(max_length=64, blank=True, default='', db_index=True)
    correlation_id = models.CharField(max_length=128, blank=True, default='', db_index=True)
    additional_metadata = models.JSONField(default=dict, blank=True)

    # Tamper-Evident Chained Cryptographic Hashes
    previous_hash = models.CharField(max_length=64, editable=False, default='0'*64)
    current_hash = models.CharField(max_length=64, editable=False, default='')

    class Meta:
        ordering = ['timestamp', 'id']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        indexes = [
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['correlation_id']),
            models.Index(fields=['employee', 'timestamp']),
        ]

    def __str__(self):
        return f"[{self.timestamp.isoformat()}] {self.event_type.upper()} | Actor: {self.actor} | Result: {self.result}"

    def calculate_payload_hash(self, prev_hash: str) -> str:
        """
        Computes deterministic SHA-256 digest over canonical representation of record fields.
        """
        emp_id = str(self.employee.id) if self.employee else ''
        meta_json = json.dumps(self.additional_metadata or {}, sort_keys=True, separators=(',', ':'))
        
        canonical_str = "|".join([
            prev_hash,
            self.timestamp.isoformat() if self.timestamp else '',
            str(self.actor or ''),
            str(self.event_type or ''),
            emp_id,
            str(self.system or ''),
            str(self.action or ''),
            str(self.previous_state or ''),
            str(self.new_state or ''),
            str(self.result or ''),
            str(self.correlation_id or ''),
            meta_json
        ])
        
        return hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()

    def save(self, *args, **kwargs):
        """
        Append-only save enforcement. Prevents updating existing audit records.
        """
        if self.pk and AuditLog.objects.filter(pk=self.pk).exists():
            raise ValidationError("AuditLog records are append-only and cannot be updated.")

        if not self.timestamp:
            self.timestamp = timezone.now()

        # Compute tamper-evident hash chain from previous record
        latest_record = AuditLog.objects.order_by('timestamp', 'id').last()
        if latest_record and latest_record.current_hash:
            self.previous_hash = latest_record.current_hash
        else:
            self.previous_hash = '0' * 64

        self.current_hash = self.calculate_payload_hash(self.previous_hash)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Append-only delete enforcement. Prohibits deleting audit records.
        """
        raise ValidationError("AuditLog records are append-only and cannot be deleted.")
