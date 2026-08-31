---
activation: Always On
---
# Guardrails Rule
last verified against repo: 2026-08-28

## Enforced Oxlint Rules (from .oxlintrc.json)
- `react/rules-of-hooks`: Error. React Hooks must only be called at the top level of React function components or custom hooks.
- `react/only-export-components`: Warn. Export only components from component files (allowConstantExport enabled).

## Hard Workspace Guardrails
- **Zero Backend Alteration during Frontend Tasks**: Do not modify Django models, serializers, or endpoints when working on frontend tasks.
- **No Unsolicited API Integration**: Do not connect frontend components to live backend endpoints unless explicitly instructed.
- **No Bypassing Common Components**: Always use existing components in `frontend/src/components/common/` (`StatusBadge`, `SeverityBadge`, `StatCard`) instead of reimplementing ad-hoc badge elements.
- **Single Source of Mock Data**: Do not embed inline mock objects inside page components; always import from `frontend/src/data/mockData.js`.
