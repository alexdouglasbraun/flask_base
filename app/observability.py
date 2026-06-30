import json
import logging
import sys
import time
from datetime import datetime, timezone

from flask import g, request
from flask.signals import got_request_exception


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for key in (
            "method",
            "path",
            "status_code",
            "duration_ms",
            "remote_addr",
            "request_id",
            "user_agent",
            "exception_type",
        ):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_logging(app):
    log_level = getattr(logging, app.config["LOG_LEVEL"].upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    app.logger.handlers.clear()
    app.logger.propagate = True
    app.logger.setLevel(log_level)

    logging.getLogger("gunicorn.error").handlers.clear()
    logging.getLogger("gunicorn.error").propagate = True
    logging.getLogger("gunicorn.access").handlers.clear()
    logging.getLogger("gunicorn.access").propagate = True

    register_request_logging(app)


def register_request_logging(app):
    @app.before_request
    def start_request_timer():
        g.request_started_at = time.perf_counter()
        g.request_id = request.headers.get("X-Request-ID")

    @app.after_request
    def log_request(response):
        if not app.config["LOG_HEALTH_CHECKS"] and request.endpoint in {"main.health", "api.v1.health"}:
            return response

        duration_ms = round((time.perf_counter() - g.request_started_at) * 1000, 2)
        app.logger.info(
            "request completed",
            extra={
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "remote_addr": request.headers.get("X-Forwarded-For", request.remote_addr),
                "request_id": g.request_id,
                "user_agent": request.user_agent.string,
            },
        )
        return response

    def log_exception(sender, exception, **extra):
        app.logger.exception(
            "unhandled exception",
            extra={
                "method": request.method,
                "path": request.path,
                "remote_addr": request.headers.get("X-Forwarded-For", request.remote_addr),
                "request_id": getattr(g, "request_id", None),
                "exception_type": type(exception).__name__,
            },
        )

    got_request_exception.connect(log_exception, app)
