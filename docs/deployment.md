# ReconcileOS — Production Configuration and Deployment Guide

This guide details the production architecture, configuration management, database setup, static asset handling, and security hardening for ReconcileOS.

---

## 1. Architecture & Serving Responsibilities

ReconcileOS follows a decoupled enterprise architecture:

- **Backend API & Administration (Django 5.1 / Python 3.14+)**:
  - Exposes REST APIs (`/api/v1/*`) and the Django Admin portal (`/admin/`).
  - Served via a production WSGI HTTP server (e.g., **Gunicorn** on Linux containers / VMs, or **Waitress** on Windows Server).
  - Admin and REST framework static assets are compressed and served directly via **WhiteNoise**.
  - Enforces invariant evaluation, mandatory human approvals, atomic repair execution, and SHA-256 tamper-evident audit chains.

- **Frontend Application (React 19 / Vite 8)**:
  - Client-side Single Page Application (SPA).
  - Production build compiled via `npm run build` into `frontend/dist/`.
  - Served at the edge via a reverse proxy (e.g., **NGINX**, **Caddy**, **Cloudflare Pages**, or **AWS S3 + CloudFront**) or proxied to the backend.

---

## 2. Environment Configuration & Variables

ReconcileOS relies on 12-factor environment configuration. Copy `.env.example` to `.env` for local testing. In production, pass environment variables directly via your container orchestrator (Kubernetes, ECS, Docker Compose) or secrets manager.

### Required Production Variables (`DEBUG=False`)

| Variable | Description | Example / Default |
|---|---|---|
| `DEBUG` | Core execution mode. **Must be `False` in production.** | `False` |
| `SECRET_KEY` | Cryptographic secret for Django sessions and token signatures. **Application refuses to start if missing, default, or prefixed with `django-insecure-`.** | 50+ character random string |
| `ALLOWED_HOSTS` | Comma-separated list of hostnames or domains this application is permitted to serve. **Mandatory when `DEBUG=False`.** | `api.reconcileos.example.com` |
| `ENABLE_HTTPS` | Enables SSL redirection, HSTS headers, and secure session/CSRF cookies. Set to `True` when terminating SSL at proxy/app. | `True` |

### Database Configuration (PostgreSQL)

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | Standard 12-factor connection string. Takes precedence over discrete `DB_*` variables. | `postgres://user:pass@host:5432/dbname` |
| `DB_ENGINE` | Explicit engine selection (`postgres` or `sqlite`). | `sqlite` (fallback) |
| `DB_NAME` | Database name. | `reconcileos_db` |
| `DB_USER` | PostgreSQL username. | `postgres` |
| `DB_PASSWORD` | PostgreSQL password. | — |
| `DB_HOST` | Database host. | `localhost` |
| `DB_PORT` | Database port. | `5432` |
| `DB_CONN_MAX_AGE` | Persistent connection age in seconds (connection pooling). | `600` (in prod) |

### Network & Security Settings

| Variable | Description | Default |
|---|---|---|
| `CORS_ALLOWED_ORIGINS` | Comma-separated list of permitted browser origins. Wildcards (`*`) are strictly prohibited when `DEBUG=False`. | `https://app.reconcileos.example.com` |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated list of trusted origins for CSRF protection. | `https://app.reconcileos.example.com` |
| `SECURE_HSTS_SECONDS` | HTTP Strict Transport Security duration. | `31536000` (1 year) |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS` | Include subdomains in HSTS header. | `True` |
| `SECURE_HSTS_PRELOAD` | Allow browser HSTS preload list registration. | `True` |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | Lifetime of SimpleJWT access tokens. | `60` |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | Lifetime of SimpleJWT refresh tokens. | `7` |

---

## 3. Database Readiness (PostgreSQL)

ReconcileOS supports enterprise PostgreSQL through Django 5.1's native `psycopg` (v3) backend.

### Setting Up PostgreSQL
1. Create a dedicated database and user:
   ```sql
   CREATE DATABASE reconcileos_db;
   CREATE USER reconcileos_app WITH ENCRYPTED PASSWORD 'replace_with_strong_password';
   GRANT ALL PRIVILEGES ON DATABASE reconcileos_db TO reconcileos_app;
   ALTER DATABASE reconcileos_db OWNER TO reconcileos_app;
   ```
2. Set `DATABASE_URL` or `DB_ENGINE=postgres`:
   ```bash
   DATABASE_URL=postgres://reconcileos_app:replace_with_strong_password@db.internal:5432/reconcileos_db
   ```
3. Run migrations:
   ```bash
   python manage.py migrate
   ```

*Note on Local Development & Tests: When neither `DATABASE_URL` nor `DB_ENGINE=postgres` is set, ReconcileOS defaults seamlessly to SQLite (`db.sqlite3`).*

---

## 4. Static Files & Production Web Serving

ReconcileOS uses **WhiteNoise** for high-efficiency, compressed, manifest-hashed static file delivery without needing a separate asset proxy.

### 1. Collect Static Files
Run before launching the WSGI server:
```bash
python manage.py collectstatic --noinput
```
This gathers Django Admin and DRF UI assets into `staticfiles/` and generates gzip/brotli pre-compressed versions with long-term cache headers (`Cache-Control: max-age=31536000, public`).

### 2. WSGI Server Execution (Gunicorn)
Run the application using Gunicorn behind an SSL-terminating reverse proxy (such as NGINX or AWS ALB):
```bash
gunicorn reconcileos.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --threads 2 \
  --timeout 60 \
  --access-logfile - \
  --error-logfile -
```

### 3. Reverse Proxy Configuration (NGINX Snippet)
```nginx
server {
    listen 443 ssl http2;
    server_name api.reconcileos.example.com;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/api.reconcileos.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.reconcileos.example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

---

## 5. Frontend Production Build

The React single-page application is compiled into static distribution files:

```bash
cd frontend
npm ci
npm run lint
npm run build
```
Output directory: `frontend/dist/`.  
Deploy these static assets to your CDN, S3 bucket, or NGINX root directory.

---

## 6. Pre-Flight Verification & Deployment Checks

Before promoting ReconcileOS to production, execute the automated checks:

1. **Verify Django Deployment Health:**
   ```bash
   DEBUG=False \
   SECRET_KEY="<strong-random-key>" \
   ALLOWED_HOSTS="api.reconcileos.example.com" \
   ENABLE_HTTPS=True \
   python manage.py check --deploy
   ```
   *Expected result: 0 issues, 0 silenced.*

2. **Verify Automated Test Suite:**
   ```bash
   python manage.py test apps.workflows apps.reconciliation apps.audit apps.connectors
   ```
   *Expected result: 107 tests passing.*

3. **Verify Frontend Lint & Build:**
   ```bash
   cd frontend && npm run lint && npm run build
   ```
