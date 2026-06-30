from flask import Blueprint

from .saml_routes import saml

auth = Blueprint("auth", __name__, url_prefix="/auth")
auth.register_blueprint(saml)

from . import routes
