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

## 2026-10-19 — Phase 6: Final Regression, Security & Browser Acceptance Audit
- **Decision**: Perform comprehensive, evidence-based acceptance audit across security guardrails, workflow contracts, concurrency controls, production configuration, and database engines without mutating business logic or deploying. Document findings in `docs/phase6_acceptance_report.md`.
- **Why**: Ensures that all features across Phases 1 through 5 and the UI redesign remain completely intact, provably secure, and regression-free before final handoff.

