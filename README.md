# Flask Base

A production-oriented Flask starter app with:

- App factory layout
- Nested Flask blueprints
- Bootstrap templates
- Role-based access control with SCIM-ready provisioning endpoints
- SAML single sign-on hooks via `python3-saml`
- SQLite by default for local development
- PostgreSQL-ready via SQLAlchemy and Flask-Migrate
- Health/readiness endpoints for Kubernetes
- Gunicorn container entrypoint
- Kubernetes manifests for load-balanced app deployment

## Local setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
flask --app wsgi db upgrade
flask --app wsgi run
```

By default the local app uses SQLite at `instance/app.db`. Set `DATABASE_URL` when you are ready to switch to PostgreSQL.

For a local PostgreSQL dependency, use Docker Compose:

```powershell
docker compose --profile postgres up --build
```

## Required configuration

The app reads configuration from environment variables:

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Flask session signing key |
| `DATABASE_URL` | Optional database connection string; defaults to local SQLite when unset |
| `SCIM_BEARER_TOKEN` | Bearer token required for `/scim/v2` provisioning endpoints |
| `SERVER_NAME` | Public host used by SAML URLs |
| `TRUST_PROXY_HEADERS` | Set to `true` behind an Ingress/load balancer |
| `SAML_SP_ENTITY_ID` | Service provider entity ID |
| `SAML_SP_ACS_URL` | Assertion consumer service URL |
| `SAML_SP_SLS_URL` | Single logout service URL |
| `SAML_IDP_ENTITY_ID` | Identity provider entity ID |
| `SAML_IDP_SSO_URL` | Identity provider SSO URL |
| `SAML_IDP_SLO_URL` | Identity provider logout URL |
| `SAML_IDP_X509_CERT` | Identity provider signing certificate |

## Kubernetes

Update image names, host names, and secrets in `k8s/`, then apply:

```powershell
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.example.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/migrate-job.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
```

Replace `secret.example.yaml` with your platform's secret manager or sealed-secret workflow before production use.

## Database migrations

Create or update the local SQLite database:

```powershell
flask --app wsgi db upgrade
```

Then register a local user at `/auth/register` and sign in at `/auth/login`.
Local accounts are created as administrators. SCIM-provisioned users default to the `user` role unless a SCIM `roles` value of `admin` is supplied.

Example SCIM user payload:

```json
{
  "userName": "person@example.com",
  "displayName": "Example Person",
  "active": true,
  "roles": [{ "value": "admin", "primary": true }]
}
```

Generate future migrations after model changes:

```powershell
flask --app wsgi db migrate -m "initial schema"
flask --app wsgi db upgrade
```

In Kubernetes, run migrations as a Job or release hook before rolling out a new image.
