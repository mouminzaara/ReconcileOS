# ReconcileOS Comprehensive Audit Logging Architecture

## Overview
ReconcileOS implements an automated, continuous, append-only, and tamper-evident audit logging stream. Every automated decision, rule evaluation, integrity violation detection, repair plan creation, approval decision, repair execution, retry attempt, verification check, and violation resolution generates an immutable audit log record.

---

## Audit Record Schema

Each `AuditLog` record contains the following standardized attributes:

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `id` | UUID | Unique primary key for the audit entry. |
| `timestamp` | DateTime | UTC timestamp when the event was recorded (ISO 8601). |
| `actor` | String | Initiating entity (e.g. `'ReconciliationEngine'`, `'RepairExecutor'`, `'PostRepairVerifier'`, user username/email). |
| `event_type` | String | Event classification enum code. |
| `employee` | FK (Employee) | Optional relation to the target employee identity. |
| `system` | String | Target downstream connector or system (`'VPN'`, `'GitHub'`, `'Cloud IAM'`, `'Slack'`). |
| `action` | String | Standardized action string (e.g. `'EVALUATE_RULE'`, `'DISABLE VPN ACCESS'`). |
| `previous_state` | String | Observed or previous state prior to action. |
| `new_state` | String | Expected or target state after action. |
| `result` | String | Event outcome (`'SUCCESS'`, `'FAILED'`, `'DRIFT_DETECTED'`, `'COMPLIANT'`, `'RESOLVED'`). |
| `correlation_id` | String / UUID | End-to-end operation identifier linking pipeline events across modules. |
| `additional_metadata` | JSON | Arbitrary contextual metadata payload (e.g. rule codes, plan IDs, error output). |
| `previous_hash` | SHA-256 (Hex) | Cryptographic hash of the preceding audit record (`'0'*64` for root record). |
| `current_hash` | SHA-256 (Hex) | Cryptographic SHA-256 digest over current record fields concatenated with `previous_hash`. |

---

## Supported Event Taxonomy (`AuditEventType`)

1. **`rule_evaluated`**: Logged when a security rule is evaluated against employee system state.
2. **`violation_detected`**: Logged when an authorization drift / integrity violation is detected.
3. **`repair_plan_created`**: Logged when a deterministic remediation plan is created.
4. **`approval_requested`**: Logged when a human-in-the-loop approval request is generated.
5. **`repair_approved`**: Logged when an approval request is approved by an authorized administrator.
6. **`repair_rejected`**: Logged when an approval request is rejected by an administrator.
7. **`repair_executed`**: Logged when downstream connector repair execution succeeds.
8. **`execution_failed`**: Logged when repair plan execution fails.
9. **`retry_performed`**: Logged when a transient execution failure triggers a bounded retry attempt.
10. **`verification_performed`**: Logged when post-repair empirical verification passes.
11. **`verification_failed`**: Logged when post-repair empirical verification fails.
12. **`violation_resolved`**: Logged when an integrity violation is resolved and closed.

---

## Append-Only Immutability Safeguards

To prevent tampering by unauthorized users or accidental modifications:
- **Model-Level Save Safeguard**: Calling `save()` on an existing record (`pk` exists) raises `ValidationError("AuditLog records are append-only and cannot be updated.")`.
- **Model-Level Delete Safeguard**: Calling `delete()` on an `AuditLog` instance raises `ValidationError("AuditLog records are append-only and cannot be deleted.")`.
- **REST API Scoping**: Exposed exclusively via `ReadOnlyModelViewSet` (only `GET` queries allowed; `POST`, `PUT`, `PATCH`, `DELETE` are disallowed).

---

## Tamper-Evident Cryptographic Hash Chaining

Audit logs are cryptographically linked using SHA-256 digest hashing:

$$H_i = \text{SHA256}(H_{i-1} \parallel \text{timestamp} \parallel \text{actor} \parallel \text{event\_type} \parallel \text{employee\_id} \parallel \text{system} \parallel \text{action} \parallel \text{previous\_state} \parallel \text{new\_state} \parallel \text{result} \parallel \text{correlation\_id} \parallel \text{JSON(metadata)})$$

If any historical audit record is altered or deleted in database storage, the hash chain breaks.

### Chain Integrity Verification

The system provides `AuditLogger.verify_chain_integrity()` and an API endpoint `/api/v1/audit/logs/verify_chain/` which re-computes every link in sequence to verify tamper evidence.

```json
// GET /api/v1/audit/logs/verify_chain/
{
    "is_valid": true,
    "message": "Cryptographic chain integrity verified. All 42 records intact.",
    "details": {
        "total_records": 42,
        "verified_records": 42,
        "head_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    }
}
```
