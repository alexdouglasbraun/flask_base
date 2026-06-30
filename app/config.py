import os
from datetime import timedelta


def _database_url():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        return "sqlite:///app.db"

    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql://", 1)

    return database_url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
    }
    DEBUG = os.environ.get("FLASK_DEBUG", "").lower() in {"1", "true", "yes", "on"}
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    LOG_HEALTH_CHECKS = os.environ.get("LOG_HEALTH_CHECKS", "").lower() in {"1", "true", "yes", "on"}
    DEFAULT_ADMIN_EMAIL = os.environ.get("DEFAULT_ADMIN_EMAIL", "admin@admin.com")
    DEFAULT_ADMIN_PASSWORD = os.environ.get("DEFAULT_ADMIN_PASSWORD", "admin")
    SAML_ENABLED = os.environ.get("SAML_ENABLED", "").lower() in {"1", "true", "yes", "on"}
    SAML_STRICT = os.environ.get("SAML_STRICT", "true").lower() in {"1", "true", "yes", "on"}
    SAML_DEBUG = os.environ.get("SAML_DEBUG", "").lower() in {"1", "true", "yes", "on"}
    SAML_SP_ENTITY_ID = os.environ.get("SAML_SP_ENTITY_ID", "http://localhost:5000/auth/saml/metadata")
    SAML_SP_ACS_URL = os.environ.get("SAML_SP_ACS_URL", "http://localhost:5000/auth/saml/acs")
    SAML_SP_SLS_URL = os.environ.get("SAML_SP_SLS_URL", "http://localhost:5000/auth/logout")
    SAML_IDP_ENTITY_ID = os.environ.get("SAML_IDP_ENTITY_ID", "")
    SAML_IDP_SSO_URL = os.environ.get("SAML_IDP_SSO_URL", "")
    SAML_IDP_SLO_URL = os.environ.get("SAML_IDP_SLO_URL", "")
    SAML_IDP_X509_CERT = os.environ.get("SAML_IDP_X509_CERT", "")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRES_MINUTES = int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "60"))
