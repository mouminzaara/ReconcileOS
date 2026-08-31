# Decision Log
last verified against repo: 2026-08-28

## 2026-08-28 — Initial Architecture & UI Shell Setup
- **Decision**: Adopt standalone Vite + React project inside `./frontend/` for ReconcileOS UI shell.
- **Why**: Keeps frontend cleanly isolated from Django templates while supporting rapid hot-reloading and modern ESM bundling.
- **Alternatives Considered**: Django HTML Templates (rejected to support modern enterprise SPA aesthetics and separate REST API integration).

## 2026-08-28 — Zero-Trust Default Status for VPNAccess Connector
- **Decision**: Set default `VPNAccess.status` to `DISABLED` and auto-initialize unprovisioned employee queries to `DISABLED`.
- **Why**: Enforces enterprise least-privilege security principle. Employees should not receive network access until intentionally enabled.
