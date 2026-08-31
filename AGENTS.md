# AGENTS.md — ReconcileOS Workspace Entry Point
last verified against repo: 2026-08-28

## Project Overview
ReconcileOS is an automated continuous integrity and self-healing platform engineered to prevent authorization drift, stale credentials, and unauthorized access across distributed enterprise applications (such as HR, VPN, GitHub, Cloud IAM, and Slack).

## Verified Tech Stack
- **Backend**: Python 3.14+ / Django 5.1.x / Django REST Framework (DRF) 3.17.x
- **Authentication**: SimpleJWT & Django Session Auth
- **Database**: SQLite (dev) / PostgreSQL-ready
- **Frontend**: React 19.2.8 / Vite 8.2.2 / React Router 7.18.2 / Lucide React 1.35.0 / Oxlint 1.79.0

## Frontend Directory Map (`frontend/src/`)
- `assets/` — Static assets and SVG icons
- `components/` — Reusable layout and atomic design components (`layout/`, `common/`, `dashboard/`)
- `data/` — Centralized mock data payload definitions (`mockData.js`)
- `pages/` — Top-level domain page components for all 9 routes
- `styles/` — Global styling sheets (`layout.css`, `components.css`)

## Rules & Memory Pointers
- `.agents/rules/guardrails.md` — Read automatically (Always On) for oxlint rules and strict don'ts.
- `.agents/rules/code-style.md` — Read when working in `frontend/src/**` for component and styling conventions.
- `.agents/rules/security.md` — Read when dealing with authentication, zero-trust state defaults, or security models.
- `.agents/memory-bank/architecture.md` — Read when modifying core data flow or cross-module integration.
- `.agents/memory-bank/decisions.md` — Read to inspect or append architectural decisions.
- `.agents/memory-bank/progress.md` — Read to check milestone completion status.
- `.agents/memory-bank/context.md` — Read for active-session scratch notes.

## Session Protocol
- **Start of session**: Read root `AGENTS.md` first. Rules load automatically per activation mode.
- **End of session**: If a real decision was made, append to `.agents/memory-bank/decisions.md`; update `progress.md`; prune `context.md`.
