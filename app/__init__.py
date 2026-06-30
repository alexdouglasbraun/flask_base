from flask import Flask

from .api import api
from .auth import auth
from .config import Config
from .extensions import db, login_manager
from .models import Role, User
from .observability import configure_logging
from .main import main


def _bootstrap_security_data(app):
    with app.app_context():
        db.create_all()

        roles_by_name = {}
        for role_name in ("Admin", "User"):
            role = Role.query.filter_by(name=role_name).first()
            if role is None:
                role = Role(name=role_name, description=f"Default {role_name.lower()} role")
                db.session.add(role)
            roles_by_name[role_name] = role

        admin_user = User.query.filter_by(email=app.config["DEFAULT_ADMIN_EMAIL"]).first()
        if admin_user is None:
            admin_user = User(
                email=app.config["DEFAULT_ADMIN_EMAIL"],
                name="Default Admin",
                auth_provider="local",
            )
            admin_user.set_password(app.config["DEFAULT_ADMIN_PASSWORD"])
            admin_user.roles.extend([roles_by_name["Admin"], roles_by_name["User"]])
            db.session.add(admin_user)
        else:
            if not admin_user.password_hash:
                admin_user.set_password(app.config["DEFAULT_ADMIN_PASSWORD"])
            for role in roles_by_name.values():
                if role not in admin_user.roles:
                    admin_user.roles.append(role)

        db.session.commit()


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    configure_logging(app)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"

    app.register_blueprint(main)
    app.register_blueprint(api)
    app.register_blueprint(auth)

    _bootstrap_security_data(app)

    return app


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
