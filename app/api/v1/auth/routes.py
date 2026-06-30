from flask import jsonify, request
import jwt
from flask_login import current_user, login_required, logout_user

from . import auth_api
from ....auth.saml import build_saml_auth, saml_enabled
from ....services.auth import (
    authenticate_local,
    authenticate_saml_identity,
    create_access_token,
    get_authenticated_api_user,
    serialize_user,
    start_user_session,
)


def _request_payload():
    return request.get_json(silent=True) or request.form


@auth_api.post("/login")
def login():
    payload = _request_payload()
    result = authenticate_local(payload.get("email", ""), payload.get("password", ""))
    if not result.ok:
        return jsonify(error=result.message, ok=False), 401

    user = start_user_session(result.user)
    tokens = create_access_token(result.user)
    return jsonify(message=result.message, ok=True, tokens=tokens, user=user)


@auth_api.post("/logout")
@login_required
def logout():
    logout_user()
    return jsonify(message="You have been signed out.", ok=True)


@auth_api.get("/me")
def me():
    user = get_authenticated_api_user(request.headers.get("Authorization"))
    if user is None:
        return jsonify(authenticated=False, ok=True, user=None)

    return jsonify(authenticated=True, ok=True, user=serialize_user(user))


@auth_api.post("/token")
def token():
    payload = _request_payload()
    result = authenticate_local(payload.get("email", ""), payload.get("password", ""))
    if not result.ok:
        return jsonify(error=result.message, ok=False), 401

    return jsonify(message="Access token issued.", ok=True, tokens=create_access_token(result.user), user=serialize_user(result.user))


@auth_api.post("/saml/acs")
def saml_acs():
    if not saml_enabled():
        return jsonify(error="SAML login is not configured yet.", ok=False), 400

    auth_client = build_saml_auth()
    auth_client.process_response()
    errors = auth_client.get_errors()
    if errors:
        return jsonify(error="SAML authentication failed.", errors=errors, ok=False), 400

    result = authenticate_saml_identity(auth_client.get_nameid(), auth_client.get_attributes())
    if not result.ok:
        return jsonify(error=result.message, ok=False), 400

    user = start_user_session(result.user)
    tokens = create_access_token(result.user)
    return jsonify(message=result.message, ok=True, tokens=tokens, user=user)


@auth_api.get("/token/verify")
def verify_token():
    authorization_header = request.headers.get("Authorization")
    if not authorization_header:
        return jsonify(error="Missing bearer token.", ok=False), 401

    try:
        user = get_authenticated_api_user(authorization_header)
    except jwt.InvalidTokenError as exc:
        return jsonify(error=str(exc), ok=False), 401

    if user is None:
        return jsonify(error="Invalid or expired token.", ok=False), 401

    return jsonify(authenticated=True, ok=True, user=serialize_user(user))
