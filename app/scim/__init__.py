from flask import Blueprint

scim_bp = Blueprint("scim", __name__, url_prefix="/scim/v2")

from app.scim import routes  # noqa: E402,F401
