from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from flask import current_app
from flask_login import current_user, login_user

from ..extensions import db
from ..models import Role, User


@dataclass
class AuthenticationResult:
    ok: bool
    user: User | None = None
    message: str = ""


def _jwt_module():
    try:
        import jwt
    except ImportError as exc:
        raise RuntimeError("PyJWT is not installed. Install dependencies from requirements.txt.") from exc

    return jwt


def serialize_user(user):
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "auth_provider": user.auth_provider,
        "roles": [role.name for role in user.roles],
    }


def sync_default_user_role(user):
    user_role = Role.query.filter_by(name="User").first()
    if user_role and user_role not in user.roles:
        user.roles.append(user_role)


def authenticate_local(email, password):
    normalized_email = email.strip().lower()
    user = User.query.filter_by(email=normalized_email).first()
    if user is None or not user.check_password(password):
        return AuthenticationResult(ok=False, message="Invalid email or password.")

    if not user.is_active:
        return AuthenticationResult(ok=False, message="This account is inactive.")

    return AuthenticationResult(ok=True, user=user, message="Signed in successfully.")


def authenticate_saml_identity(name_id, attributes):
    email = (name_id or next(iter(attributes.get("email", [])), "")).strip().lower()
    if not email:
        return AuthenticationResult(ok=False, message="SAML response did not include an email address.")

    display_name = next(iter(attributes.get("displayName", [])), None) or next(iter(attributes.get("name", [])), None)
    user = User.query.filter((User.email == email) | (User.saml_name_id == name_id)).first()

    if user is None:
        user = User(
            email=email,
            name=display_name,
            auth_provider="saml",
            saml_name_id=name_id,
        )
        sync_default_user_role(user)
        db.session.add(user)
    else:
        user.auth_provider = "saml"
        user.saml_name_id = name_id
        user.name = user.name or display_name
        sync_default_user_role(user)

    db.session.commit()
    return AuthenticationResult(ok=True, user=user, message="Signed in with SAML.")


def start_user_session(user, remember=False):
    login_user(user, remember=remember)
    return serialize_user(user)


def create_access_token(user):
    jwt = _jwt_module()
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=current_app.config["JWT_ACCESS_TOKEN_EXPIRES_MINUTES"])
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "roles": [role.name for role in user.roles],
        "auth_provider": user.auth_provider,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "type": "access",
    }
    token = jwt.encode(
        payload,
        current_app.config["JWT_SECRET_KEY"],
        algorithm=current_app.config["JWT_ALGORITHM"],
    )
    return {
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": current_app.config["JWT_ACCESS_TOKEN_EXPIRES_MINUTES"] * 60,
    }


def decode_access_token(token):
    jwt = _jwt_module()
    payload = jwt.decode(
        token,
        current_app.config["JWT_SECRET_KEY"],
        algorithms=[current_app.config["JWT_ALGORITHM"]],
    )
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Invalid token type.")
    return payload


def get_user_from_bearer_token(authorization_header):
    if not authorization_header:
        return None

    scheme, _, token = authorization_header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None

    payload = decode_access_token(token)
    user = db.session.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        return None
    return user


def get_authenticated_api_user(authorization_header):
    token_user = get_user_from_bearer_token(authorization_header)
    if token_user is not None:
        return token_user

    if current_user.is_authenticated:
        return current_user

    return None
