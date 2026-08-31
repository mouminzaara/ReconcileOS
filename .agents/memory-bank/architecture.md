# Architecture Memory Bank
last verified against repo: 2026-08-28

## System Overview
ReconcileOS consists of a decoupled Django REST Framework backend and a React/Vite frontend shell.

### Django Modular Backend (`apps/`)
- `employees/` — System of Record HR directory (`Employee` model with `ACTIVE`/`TERMINATED` lifecycle states).
- `connectors/` — Downstream system integration connectors (`VPNAccess` model with `ENABLED`/`DISABLED` states, auto-initialization to `DISABLED`, and 1:1 binding).
- `accounts/` — Auth & JWT infrastructure.
- `rules/`, `reconciliation/`, `workflows/`, `approvals/`, `audit/` — Scaffolded engine modules for continuous integrity.

### React / Vite Frontend Shell (`frontend/`)
- Single-page application using React Router 7 for 9 primary domain views.
- Centralized static mock data payload repository in `src/data/mockData.js`.
