import os


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///app.db",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SERVER_NAME = os.getenv("SERVER_NAME")
    PREFERRED_URL_SCHEME = os.getenv("PREFERRED_URL_SCHEME", "https")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _bool_env("SESSION_COOKIE_SECURE", True)
    TRUST_PROXY_HEADERS = _bool_env("TRUST_PROXY_HEADERS", False)
    SCIM_BEARER_TOKEN = os.getenv("SCIM_BEARER_TOKEN", "")

    SAML_STRICT = _bool_env("SAML_STRICT", True)
    SAML_DEBUG = _bool_env("SAML_DEBUG", False)
    SAML_SP_ENTITY_ID = os.getenv("SAML_SP_ENTITY_ID", "")
    SAML_SP_ACS_URL = os.getenv("SAML_SP_ACS_URL", "")
    SAML_SP_SLS_URL = os.getenv("SAML_SP_SLS_URL", "")
    SAML_IDP_ENTITY_ID = os.getenv("SAML_IDP_ENTITY_ID", "")
    SAML_IDP_SSO_URL = os.getenv("SAML_IDP_SSO_URL", "")
    SAML_IDP_SLO_URL = os.getenv("SAML_IDP_SLO_URL", "")
    SAML_IDP_X509_CERT = os.getenv("SAML_IDP_X509_CERT", "")


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///app.db")
    PREFERRED_URL_SCHEME = "http"
    SESSION_COOKIE_SECURE = False


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False


class ProductionConfig(BaseConfig):
    DEBUG = False


def config_by_name(name: str | None):
    selected = name or os.getenv("FLASK_ENV", "production")
    return {
        "development": DevelopmentConfig,
        "testing": TestingConfig,
        "production": ProductionConfig,
    }.get(selected, ProductionConfig)
