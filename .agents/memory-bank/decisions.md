# Decision Log
last verified against repo: 2026-08-28

## 2026-08-28 — Initial Architecture & UI Shell Setup
- **Decision**: Adopt standalone Vite + React project inside `./frontend/` for ReconcileOS UI shell.
- **Why**: Keeps frontend cleanly isolated from Django templates while supporting rapid hot-reloading and modern ESM bundling.
- **Alternatives Considered**: Django HTML Templates (rejected to support modern enterprise SPA aesthetics and separate REST API integration).

## 2026-08-28 — Zero-Trust Default Status for VPNAccess Connector
- **Decision**: Set default `VPNAccess.status` to `DISABLED` and auto-initialize unprovisioned employee queries to `DISABLED`.
- **Why**: Enforces enterprise least-privilege security principle. Employees should not receive network access until intentionally enabled.

## 2026-10-10 — Connected Systems Live State Integration
- **Decision**: Connect `ConnectedSystemsPage` to genuine backend state via existing `api.getCollectedStates()` (`GET /api/v1/reconciliation/state/`) and `api.getViolations()` (`GET /api/v1/reconciliation/violations/`), maintaining layout and keeping "Test Connectors" safely disabled.
- **Why**: Replaces static mock data with real-time telemetry from active multi-system state collection and invariant rule evaluation, while preserving UI layout and zero backend alteration.

## 2026-10-21 — Repeatable Teacher Demo Scenario (`seed_demo_scenario`)
- **Decision**: Provide an idempotent `python manage.py seed_demo_scenario` command that generates a real drift condition for Rahul Kumar (HR: TERMINATED, VPN: ENABLED), runs the genuine ReconciliationEngine and RepairPlanner, and intentionally stops before human approval/execution.
- **Why**: Allows live teacher demonstrations to showcase the entire interactive lifecycle (Dashboard -> Violations -> Repairs -> Approvals -> Execution -> Audit Logs) without mock data or manual database edits. Includes `--reset-only` for instant resets.

## 2026-10-21 — Client-Side Multi-Entity Header Search
- **Decision**: Wire header search to existing DRF GET endpoints (`/api/v1/employees/`, `/api/v1/reconciliation/violations/`, `/api/v1/workflows/plans/`, `/api/v1/audit/logs/`) with cached, debounced client filtering and direct navigation.
- **Why**: Provides an instant, unified global search experience without creating custom backend endpoints or changing API contracts.
## 2026-10-23 — Approval to Execution & Dashboard State Synchronization
- **Decision**: Trigger repair execution and post-repair empirical verification immediately upon approval request approval in `POST /api/v1/approvals/<id>/approve/` via `ApprovalService.approve_request(execute_repair=True)`. Fix Dashboard pending count calculation and drift anomaly callout filter.
- **Why**: Aligns the UI "Approve & Execute" action with the intended end-to-end workflow so that downstream target connectors mutate, post-repair verification resolves the violation, audit events are recorded, and the Dashboard immediately reflects current clean state without drift re-occurrence.

## 2026-10-24 — Phase 2: Employee Termination Audit & Reconciliation Integration + Audit RBAC
- **Decision**: Add `EMPLOYEE_TERMINATED` to `AuditEventType` and cryptographically record employee terminations atomically. Trigger employee-scoped reconciliation and repair planning immediately upon successful termination, returning detected drift and pending repair plans in the API response. Standardize `AuditLogViewSet` permissions with `IsViewerUserRole` on list/retrieve and `IsAdminUserRole` on `verify_chain`.
- **Why**: Eliminates the compliance audit gap on employee offboarding, closes the reconciliation delay without requiring manual page navigation, preserves mandatory human approval for repairs, and enforces least-privilege RBAC on audit endpoints.

## 2026-10-24 — Phase 4: Dedicated End-to-End Functional Test Suite (`test_phase4_e2e_audit.py`)
- **Decision**: Create an isolated test suite `Phase4EndToEndFunctionalAuditTests` covering Workflows 1–9 using Django's test framework with clean transactional rollback and dedicated test user fixtures.
- **Why**: Allows deterministic, automated verification of authentication, lifecycle transitions, violation deduplication, approval authorization, retry policies, cryptographic tamper detection, connector health checks, and pagination on a disposable database without risking live external systems.

## 2026-10-24 — Phase 5: Production Readiness & KPI Synchronization Guard
- **Decision**: Ensure Dashboard KPI metrics derive directly from backend pagination `count` fields rather than client-side single-page slice lengths. Clean up unused handlers across all query-driven search pages. Document exact production deployment prerequisites and manual verification checklists.
- **Why**: Guarantees truthful KPI reporting across large enterprise datasets, maintains 0-error lint cleanliness, and provides verifiable evidence for production deployment readiness.

## 2026-10-24 — Phase 6: Premium Enterprise Admin Design System Standard
- **Decision**: Shift from informal landing-page pill styling and beige palette to an authentic enterprise admin aesthetic: sophisticated lavender base (`#EFE9F8`), crisp white surfaces (`#FFFFFF`), muted lavender borders (`#DCD3EF`), dark text (`#1F192C`), restrained secondary text (`#584F66`), and semantic status colors (Coral, Amber, Mint) reserved strictly for meaningful indicators. Normalize border radii to crisp enterprise standards: 6px buttons, 6px inputs, 10px cards, reserving pill radii (`9999px`) strictly for status badges. Scale down oversized 36px/44px headings to a proportional 24px/700-weight hierarchy with balanced spacing.
- **Why**: Delivers an authentic enterprise product aesthetic suitable for an enterprise integrity and governance platform while strictly preserving all existing routes, business logic, API integrations, and role-based access control.

