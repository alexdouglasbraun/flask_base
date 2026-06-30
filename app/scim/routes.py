from datetime import datetime, timezone
from functools import wraps

from flask import current_app, jsonify, request

from app.extensions import db
from app.models import Role, User
from app.scim import scim_bp

SCIM_USER_SCHEMA = "urn:ietf:params:scim:schemas:core:2.0:User"


def scim_token_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        expected_token = current_app.config["SCIM_BEARER_TOKEN"]
        auth_header = request.headers.get("Authorization", "")
        if not expected_token or auth_header != f"Bearer {expected_token}":
            return _scim_error("Unauthorized", 401)
        return view(*args, **kwargs)

    return wrapped


@scim_bp.get("/ServiceProviderConfig")
@scim_token_required
def service_provider_config():
    return jsonify(
        schemas=["urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig"],
        documentationUri="https://example.com/docs/scim",
        patch={"supported": True},
        bulk={"supported": False, "maxOperations": 0, "maxPayloadSize": 0},
        filter={"supported": True, "maxResults": 100},
        changePassword={"supported": False},
        sort={"supported": False},
        etag={"supported": False},
        authenticationSchemes=[
            {
                "type": "oauthbearertoken",
                "name": "Bearer Token",
                "description": "Static bearer token configured with SCIM_BEARER_TOKEN.",
                "primary": True,
            }
        ],
    )


@scim_bp.get("/Users")
@scim_token_required
def list_users():
    start_index = max(int(request.args.get("startIndex", 1)), 1)
    count = max(int(request.args.get("count", 100)), 1)
    query = User.query

    filter_value = request.args.get("filter", "")
    if filter_value.startswith('userName eq "'):
        email = filter_value.removeprefix('userName eq "').removesuffix('"').strip().lower()
        query = query.filter_by(email=email)

    users = query.order_by(User.id).offset(start_index - 1).limit(count).all()
    total_results = query.count()
    return jsonify(
        schemas=["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        totalResults=total_results,
        startIndex=start_index,
        itemsPerPage=len(users),
        Resources=[_to_scim_user(user) for user in users],
    )


@scim_bp.post("/Users")
@scim_token_required
def create_user():
    payload = request.get_json(silent=True) or {}
    email = _email_from_payload(payload)
    if not email:
        return _scim_error("userName or primary email is required.", 400)

    user = User.query.filter_by(email=email).first()
    if user is None:
        user = User(email=email)
        db.session.add(user)

    _apply_scim_payload(user, payload)
    db.session.commit()
    return jsonify(_to_scim_user(user)), 201


@scim_bp.get("/Users/<int:user_id>")
@scim_token_required
def get_user(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        return _scim_error("User not found.", 404)
    return jsonify(_to_scim_user(user))


@scim_bp.put("/Users/<int:user_id>")
@scim_token_required
def replace_user(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        return _scim_error("User not found.", 404)

    payload = request.get_json(silent=True) or {}
    _apply_scim_payload(user, payload)
    db.session.commit()
    return jsonify(_to_scim_user(user))


@scim_bp.patch("/Users/<int:user_id>")
@scim_token_required
def patch_user(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        return _scim_error("User not found.", 404)

    payload = request.get_json(silent=True) or {}
    for operation in payload.get("Operations", []):
        value = operation.get("value", {})
        if isinstance(value, dict):
            _apply_scim_payload(user, value)

    db.session.commit()
    return jsonify(_to_scim_user(user))


@scim_bp.delete("/Users/<int:user_id>")
@scim_token_required
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        return "", 204

    user.active = False
    db.session.commit()
    return "", 204


def _apply_scim_payload(user: User, payload: dict) -> None:
    email = _email_from_payload(payload)
    if email:
        user.email = email

    user.scim_external_id = payload.get("externalId") or user.scim_external_id
    user.active = _bool_from_payload(payload.get("active", user.active))
    user.display_name = payload.get("displayName") or _name_from_payload(payload) or user.display_name or user.email
    role_names = _role_names_from_payload(payload)
    if role_names is not None:
        user.roles = _roles_by_name(role_names)
    user.last_login_at = user.last_login_at or datetime.now(timezone.utc)


def _email_from_payload(payload: dict) -> str | None:
    user_name = payload.get("userName")
    if user_name:
        return str(user_name).strip().lower()

    for email in payload.get("emails", []):
        if email.get("primary") or email.get("value"):
            return str(email.get("value")).strip().lower()
    return None


def _name_from_payload(payload: dict) -> str | None:
    name = payload.get("name") or {}
    formatted = name.get("formatted")
    if formatted:
        return formatted

    parts = [name.get("givenName"), name.get("familyName")]
    return " ".join(part for part in parts if part) or None


def _role_names_from_payload(payload: dict) -> list[str] | None:
    if "roles" not in payload:
        return None

    role_names = []
    for role in payload.get("roles", []):
        value = str(role.get("value", "")).strip().lower()
        if value in Role.ALL:
            role_names.append(value)
    return role_names or [Role.USER]


def _roles_by_name(role_names: list[str]) -> list[Role]:
    roles = Role.query.filter(Role.name.in_(role_names)).all()
    found_names = {role.name for role in roles}
    missing_roles = [Role(name=name) for name in role_names if name not in found_names]
    db.session.add_all(missing_roles)
    return roles + missing_roles


def _bool_from_payload(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _to_scim_user(user: User) -> dict:
    return {
        "schemas": [SCIM_USER_SCHEMA],
        "id": str(user.id),
        "externalId": user.scim_external_id,
        "userName": user.email,
        "displayName": user.display_name,
        "active": user.active,
        "emails": [{"value": user.email, "primary": True}] if user.email else [],
        "roles": [{"value": role_name, "primary": role_name == Role.ADMIN} for role_name in user.role_names],
        "meta": {
            "resourceType": "User",
            "location": f"{request.url_root.rstrip('/')}/scim/v2/Users/{user.id}",
        },
    }


def _scim_error(detail: str, status: int):
    return (
        jsonify(
            schemas=["urn:ietf:params:scim:api:messages:2.0:Error"],
            detail=detail,
            status=str(status),
        ),
        status,
    )
