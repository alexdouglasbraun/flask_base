# Flask Base

A small Flask starter for DigitalOcean App Platform.

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
flask --app wsgi run --debug
```

The app will be available at `http://127.0.0.1:5000`.

## Application Layout

Routes are organized with nested blueprints:

| Module | URL prefix | Purpose |
| --- | --- | --- |
| `app.main` | `/` | Site and platform routes |
| `app.api` | `/api` | API parent blueprint |
| `app.api.v1` | `/api/v1` | Versioned API routes |

## Environment

Copy `.env.example` to `.env` for local development.

| Variable | Purpose | Default |
| --- | --- | --- |
| `SECRET_KEY` | Flask session/security key | `dev-secret-key` |
| `DATABASE_URL` | SQLAlchemy database URL | `sqlite:///app.db` |
| `FLASK_DEBUG` | Enables debug config when true | `false` |
| `LOG_LEVEL` | Python logging level | `INFO` |
| `LOG_HEALTH_CHECKS` | Log `/health` requests when true | `false` |
| `DEFAULT_ADMIN_EMAIL` | Seeded local admin email | `admin@admin.com` |
| `DEFAULT_ADMIN_PASSWORD` | Seeded local admin password | `admin` |
| `SAML_ENABLED` | Enables SAML login routes | `false` |
| `SAML_SP_ENTITY_ID` | Service provider entity ID | `http://localhost:5000/auth/saml/metadata` |
| `SAML_SP_ACS_URL` | SAML assertion consumer service URL | `http://localhost:5000/auth/saml/acs` |
| `SAML_IDP_ENTITY_ID` | Identity provider entity ID | empty |
| `SAML_IDP_SSO_URL` | Identity provider SSO URL | empty |
| `SAML_IDP_SLO_URL` | Identity provider SLO URL | empty |
| `SAML_IDP_X509_CERT` | Identity provider signing cert | empty |
| `JWT_SECRET_KEY` | Secret used to sign API JWTs | `SECRET_KEY` |
| `JWT_ALGORITHM` | JWT signing algorithm | `HS256` |
| `JWT_ACCESS_TOKEN_EXPIRES_MINUTES` | Access token lifetime in minutes | `60` |

## Database Progression

The app is set up to support the path you described:

1. `sqlite:///app.db` for local development by default
2. A development PostgreSQL instance by setting `DATABASE_URL`
3. A production PostgreSQL instance by setting `DATABASE_URL` in App Platform

Examples:

```env
DATABASE_URL=sqlite:///app.db
DATABASE_URL=postgresql://postgres:password@localhost:5432/flask_base_dev
DATABASE_URL=postgres://user:password@db.example.com:25060/defaultdb
```

If you use a `postgres://...` URL, the app normalizes it to `postgresql://...` automatically for SQLAlchemy.

## DigitalOcean App Platform

Use this run command:

```sh
gunicorn --worker-tmp-dir /dev/shm wsgi:app
```

The `/health` route returns a JSON status response and is suitable for platform health checks. The versioned API also exposes `/api/v1/health`.

App logs are written to stdout as JSON so DigitalOcean App Platform can collect them from the container log stream.

The homepage uses Bootstrap 5 with a client-side light/dark mode toggle stored in `localStorage`.

## Authentication

The app now includes:

1. Local email/password login with a seeded starter admin account
2. SAML login routes that can be enabled with environment configuration
3. Multi-role users through a many-to-many `User <-> Role` relationship

Starter roles:

- `Admin`
- `User`

Starter admin login:

- Email: `admin@admin.com`
- Password: `admin`

SAML routes:

- `/auth/saml/login`
- `/auth/saml/acs`
- `/auth/saml/metadata`

When SAML is enabled, users authenticated through the IdP are created automatically if they do not already exist and are assigned the `User` role by default.

## JWT API Auth

The auth API now supports JWT access tokens in addition to the browser session:

- `POST /api/v1/auth/login` returns a session and a JWT
- `POST /api/v1/auth/token` returns a JWT without relying on the web login flow
- `GET /api/v1/auth/me` accepts either the session cookie or `Authorization: Bearer <token>`
- `GET /api/v1/auth/token/verify` validates a bearer token
