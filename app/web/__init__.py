from flask import Blueprint

from app.auth import auth_bp
from app.main import main_bp
from app.scim import scim_bp

web_bp = Blueprint("web", __name__)
web_bp.register_blueprint(main_bp)
web_bp.register_blueprint(auth_bp)
web_bp.register_blueprint(scim_bp)
