from datetime import datetime, timezone

from flask import current_app, redirect, render_template, request, session, url_for
from flask_login import login_required, login_user, logout_user
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.settings import OneLogin_Saml2_Settings

from app.auth import auth_bp
from app.extensions import db
from app.models import Role, User


def _prepare_flask_request(req):
    url_data = req.url.split("?", 1)
    return {
        "https": "on" if req.scheme == "https" else "off",
        "http_host": req.host,
        "script_name": req.path,
        "server_port": req.environ.get("SERVER_PORT"),
        "get_data": req.args.copy(),
        "post_data": req.form.copy(),
        "query_string": url_data[1] if len(url_data) > 1 else "",
    }


def _saml_settings():
    cfg = current_app.config
    return {
        "strict": cfg["SAML_STRICT"],
        "debug": cfg["SAML_DEBUG"],
        "sp": {
            "entityId": cfg["SAML_SP_ENTITY_ID"],
            "assertionConsumerService": {
                "url": cfg["SAML_SP_ACS_URL"],
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
            },
            "singleLogoutService": {
                "url": cfg["SAML_SP_SLS_URL"],
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
        },
        "idp": {
            "entityId": cfg["SAML_IDP_ENTITY_ID"],
            "singleSignOnService": {
                "url": cfg["SAML_IDP_SSO_URL"],
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "singleLogoutService": {
                "url": cfg["SAML_IDP_SLO_URL"],
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "x509cert": cfg["SAML_IDP_X509_CERT"],
        },
        "security": {
            "authnRequestsSigned": False,
            "logoutRequestSigned": False,
            "logoutResponseSigned": False,
            "wantAssertionsSigned": True,
            "wantMessagesSigned": False,
            "wantNameId": True,
            "wantNameIdEncrypted": False,
            "wantAttributeStatement": False,
            "signatureAlgorithm": "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256",
            "digestAlgorithm": "http://www.w3.org/2001/04/xmlenc#sha256",
        },
    }


def _saml_auth():
    return OneLogin_Saml2_Auth(_prepare_flask_request(request), _saml_settings())


@auth_bp.get("/login")
def login():
    return render_template("login.html")


@auth_bp.post("/login")
def local_login():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    user = User.query.filter_by(email=email).first()

    if user is None or not user.check_password(password) or not user.active:
        return render_template("login.html", error="Invalid email or password.", email=email), 401

    user.last_login_at = datetime.now(timezone.utc)
    db.session.commit()
    login_user(user)
    return redirect(url_for("web.main.index"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    email = request.form.get("email", "").strip().lower()
    display_name = request.form.get("display_name", "").strip()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not email or not password:
        return render_template("register.html", error="Email and password are required.", email=email, display_name=display_name), 400

    if password != confirm_password:
        return render_template("register.html", error="Passwords do not match.", email=email, display_name=display_name), 400

    if User.query.filter_by(email=email).first() is not None:
        return render_template("register.html", error="An account with that email already exists.", email=email, display_name=display_name), 409

    admin_role = Role.query.filter_by(name=Role.ADMIN).first()
    user = User(email=email, display_name=display_name or email, roles=[admin_role])
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return redirect(url_for("web.main.index"))


@auth_bp.get("/saml/login")
def saml_login():
    auth = _saml_auth()
    return redirect(auth.login(return_to=url_for("web.main.index", _external=True)))


@auth_bp.post("/saml/acs")
def saml_acs():
    auth = _saml_auth()
    auth.process_response()
    errors = auth.get_errors()

    if errors or not auth.is_authenticated():
        current_app.logger.warning("SAML authentication failed: %s", errors)
        return render_template("login.html", error="SAML authentication failed."), 401

    attributes = auth.get_attributes()
    name_id = auth.get_nameid()
    email = _first_attribute(attributes, "email", "mail", "EmailAddress")
    display_name = _first_attribute(attributes, "displayName", "cn", "givenName") or email

    user = User.query.filter_by(saml_name_id=name_id).first()
    if user is None and email:
        user = User.query.filter_by(email=email).first()
    if user is None:
        user = User(saml_name_id=name_id)
        db.session.add(user)

    user.saml_name_id = name_id
    user.email = email
    user.display_name = display_name
    if not user.active:
        return render_template("login.html", error="This account is inactive."), 403

    user.last_login_at = datetime.now(timezone.utc)
    db.session.commit()

    session["saml_session_index"] = auth.get_session_index()
    session["saml_name_id"] = name_id
    login_user(user)
    return redirect(url_for("web.main.index"))


@auth_bp.get("/saml/metadata")
def saml_metadata():
    settings = OneLogin_Saml2_Settings(_saml_settings(), sp_validation_only=True)
    metadata = settings.get_sp_metadata()
    errors = settings.validate_metadata(metadata)

    if errors:
        return "\n".join(errors), 500, {"Content-Type": "text/plain"}

    return metadata, 200, {"Content-Type": "text/xml"}


@auth_bp.get("/logout")
@login_required
def logout():
    auth = _saml_auth()
    name_id = session.get("saml_name_id")
    session_index = session.get("saml_session_index")
    logout_user()
    session.clear()

    if name_id and current_app.config["SAML_IDP_SLO_URL"]:
        return redirect(auth.logout(name_id=name_id, session_index=session_index))
    return redirect(url_for("web.auth.login"))


@auth_bp.route("/saml/sls", methods=["GET", "POST"])
def saml_sls():
    auth = _saml_auth()
    auth.process_slo(delete_session_cb=lambda: session.clear())
    errors = auth.get_errors()
    if errors:
        return "\n".join(errors), 400, {"Content-Type": "text/plain"}
    return redirect(url_for("web.auth.login"))


def _first_attribute(attributes: dict[str, list[str]], *names: str) -> str | None:
    for name in names:
        values = attributes.get(name)
        if values:
            return values[0]
    return None
