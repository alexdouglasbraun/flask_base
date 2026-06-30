from flask import Blueprint

from .v1 import v1

api = Blueprint("api", __name__, url_prefix="/api")
api.register_blueprint(v1)
