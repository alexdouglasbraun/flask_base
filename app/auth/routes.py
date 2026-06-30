from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, logout_user

from . import auth
from .saml import saml_enabled
from ..services.auth import authenticate_local, start_user_session


@auth.get("/login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    return render_template("auth/login.html", saml_enabled=saml_enabled())


@auth.post("/login")
def login_post():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    result = authenticate_local(email, password)
    if not result.ok:
        flash(result.message, "danger")
        return redirect(url_for("auth.login"))

    start_user_session(result.user)
    flash(result.message, "success")
    return redirect(url_for("main.index"))


@auth.get("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("main.index"))
