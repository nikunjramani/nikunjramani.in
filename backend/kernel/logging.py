"""Structured JSON logging, which is what Cloud Logging parses into queryable fields.

Each line carries the request's trace (from Cloud Run's X-Cloud-Trace-Context header, set by
kernel/app.py's TraceContext middleware), so Cloud Logging groups a request's lines under its
request log entry."""

import json
import logging
import sys
from contextvars import ContextVar
from typing import Any

from kernel.config import get_settings

#: The current request's trace id; empty outside a request.
trace_id: ContextVar[str] = ContextVar("trace_id", default="")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        if trace := trace_id.get():
            project = get_settings().firebase_project_id
            payload["logging.googleapis.com/trace"] = f"projects/{project}/traces/{trace}"
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        extra = getattr(record, "extra_fields", None)
        if isinstance(extra, dict):
            payload.update(extra)
        return json.dumps(payload)


def configure_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
