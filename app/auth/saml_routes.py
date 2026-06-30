from flask import Blueprint
from flask import current_app, flash, redirect, url_for

from .saml import build_saml_auth, saml_enabled, saml_metadata
from ..services.auth import authenticate_saml_identity, start_user_session

saml = Blueprint("saml", __name__, url_prefix="/saml")


@saml.get("/login")
def saml_login():
    if not saml_enabled():
        flash("SAML login is not configured yet.", "warning")
        return redirect(url_for("auth.login"))

    auth_client = build_saml_auth()
    return redirect(auth_client.login())


@saml.post("/acs")
def saml_acs():
    if not saml_enabled():
        flash("SAML login is not configured yet.", "warning")
        return redirect(url_for("auth.login"))

    auth_client = build_saml_auth()
    auth_client.process_response()
    errors = auth_client.get_errors()
    if errors:
        current_app.logger.error("saml authentication failed", extra={"errors": errors})
        flash("SAML authentication failed.", "danger")
        return redirect(url_for("auth.login"))

    result = authenticate_saml_identity(auth_client.get_nameid(), auth_client.get_attributes())
    if not result.ok:
        flash(result.message, "danger")
        return redirect(url_for("auth.login"))

    start_user_session(result.user)
    flash(result.message, "success")
    return redirect(url_for("main.index"))


@saml.get("/metadata")
def metadata():
    if not current_app.config["SAML_ENABLED"]:
        return current_app.response_class("SAML is disabled.", mimetype="text/plain", status=404)

    return current_app.response_class(saml_metadata(), mimetype="text/xml")
