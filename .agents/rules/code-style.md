---
activation: Glob: frontend/src/**
---
# Frontend Code Style Rule
last verified against repo: 2026-08-28

## Component Naming & Structure
- **PascalCase**: Name all component files using `PascalCase.jsx` (e.g., `StatusBadge.jsx`, `SeverityBadge.jsx`, `DashboardPage.jsx`).
- **Named Exports**: Prefer explicit named exports (`export function StatusBadge() {}`) over default exports for components.
- **Props Shapes**:
  - `StatusBadge`: accepts `status` string (`ACTIVE`, `TERMINATED`, `ENABLED`, `DISABLED`, `HEALTHY`, `DRIFT_DETECTED`).
  - `SeverityBadge`: accepts `severity` string (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`).
  - `StatCard`: accepts `title`, `value`, `subtext`, `icon`, `variant`.

## Styling Approach
- Use CSS variables defined in `src/index.css` (`--bg-dark`, `--bg-card`, `--accent-blue`, `--status-success`, `--status-danger`).
- Component layout styles belong in `src/styles/layout.css`.
- Reusable UI element styles belong in `src/styles/components.css`.
- Avoid inline style blocks except for dynamic background or icon colors.
