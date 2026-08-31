---
activation: Model Decision
---
# Security & Zero-Trust Guidelines
last verified against repo: 2026-08-28

## Zero-Trust Default State Policy
- In accordance with enterprise least-privilege standards, downstream connector state models (`VPNAccess`) must default to `DISABLED` upon initialization.
- Never auto-provision access as `ENABLED` without explicit action or authorization flow.

## API Authentication & CORS
- Backend API authentication uses SimpleJWT (`rest_framework_simplejwt`).
- CORS headers are controlled via `django-cors-headers` in `reconcileos/settings.py`.
