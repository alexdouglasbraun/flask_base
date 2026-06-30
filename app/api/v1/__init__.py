from flask import Blueprint

from .auth import auth_api

v1 = Blueprint("v1", __name__, url_prefix="/v1")
v1.register_blueprint(auth_api)

from . import routes
