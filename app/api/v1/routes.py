from flask import jsonify

from . import v1


@v1.get("/")
def index():
    return jsonify(
        api="flask-base",
        status="ok",
        version="v1",
    )


@v1.get("/health")
def health():
    return jsonify(
        status="healthy",
        version="v1",
    )
