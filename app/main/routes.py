from flask import jsonify, render_template
from flask_login import current_user

from . import main


@main.get("/")
def index():
    return render_template("main/index.html", current_user=current_user)


@main.get("/health")
def health():
    return jsonify(status="healthy")
