import os

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from app.config import config_by_name
from app.extensions import db, login_manager, migrate


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_by_name(config_name))
    os.makedirs(app.instance_path, exist_ok=True)

    if app.config["TRUST_PROXY_HEADERS"]:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "web.auth.login"

    from app import models  # noqa: F401
    from app.web import web_bp

    app.register_blueprint(web_bp)

    return app
