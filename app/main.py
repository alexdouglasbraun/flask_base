from flask import Blueprint, current_app, jsonify, render_template, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Role
from app.rbac import role_required

main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index():
    return render_template("index.html", user=current_user)


@main_bp.get("/settings")
@login_required
def settings():
    saml_setup = {
        "metadata_url": url_for("web.auth.saml_metadata", _external=True),
        "login_url": url_for("web.auth.saml_login", _external=True),
        "acs_url": current_app.config["SAML_SP_ACS_URL"] or url_for("web.auth.saml_acs", _external=True),
        "sls_url": current_app.config["SAML_SP_SLS_URL"] or url_for("web.auth.saml_sls", _external=True),
        "sp_entity_id": current_app.config["SAML_SP_ENTITY_ID"] or url_for("web.auth.saml_metadata", _external=True),
        "idp_entity_id": current_app.config["SAML_IDP_ENTITY_ID"],
        "idp_sso_url": current_app.config["SAML_IDP_SSO_URL"],
        "idp_slo_url": current_app.config["SAML_IDP_SLO_URL"],
        "idp_cert_configured": bool(current_app.config["SAML_IDP_X509_CERT"]),
    }
    scim_setup = {
        "tenant_url": url_for("web.scim.service_provider_config", _external=True).removesuffix("/ServiceProviderConfig"),
        "service_provider_config_url": url_for("web.scim.service_provider_config", _external=True),
        "users_url": url_for("web.scim.list_users", _external=True),
        "bearer_token_configured": bool(current_app.config["SCIM_BEARER_TOKEN"]),
    }
    return render_template("settings.html", user=current_user, saml_setup=saml_setup, scim_setup=scim_setup)


@main_bp.get("/admin")
@role_required(Role.ADMIN)
def admin():
    return render_template("admin.html", user=current_user)


@main_bp.get("/healthz")
def healthz():
    return jsonify(status="ok")


@main_bp.get("/readyz")
def readyz():
    db.session.execute(db.text("select 1"))
    return jsonify(status="ready")
