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

## 2026-10-10 — UI Theme Unification & Login Page Redesign
- **Decision**: Redesign the login page as a premium split-panel layout (decorative brand left panel + form right panel) with matching warm beige/lavender gradient identity from `landing.css`. Consolidate micro-animations (fadeInUp page transitions, card hover lifts, button press feedback, input focus glows) into `index.css` for unified use across all routes.
- **Why**: The login page was the visual weakest link — a plain centered card that broke the premium feel established by the landing page and dashboard. The split layout with animated orbs, glassmorphic feature pills, and consistent gradient creates a seamless visual journey from landing → login → dashboard. Global micro-animations add the "alive" feeling that makes the enterprise UI feel responsive and polished.

