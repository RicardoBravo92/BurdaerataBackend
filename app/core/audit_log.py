import json
import logging
import time
import uuid
from contextvars import ContextVar
from typing import Any, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("audit")
audit_logger = logging.getLogger("audit.security")


# Context variable to store request ID across async calls
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    """Get the current request ID."""
    return request_id_var.get("")


def set_request_id(request_id: str) -> None:
    """Set the current request ID."""
    request_id_var.set(request_id)


class AuditLogMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests with structured audit data."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        set_request_id(request_id)

        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        # Skip health checks and static files from audit log
        skip_paths = {"/health", "/docs", "/redoc", "/openapi.json"}
        should_log = request.url.path not in skip_paths

        if should_log:
            audit_logger.info(
                "HTTP request",
                extra={
                    "audit": True,
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": dict(request.query_params),
                    "client_ip": client_ip,
                    "user_agent": user_agent,
                },
            )

        try:
            response: Response = await call_next(request)
        except Exception as e:
            duration = time.time() - start_time
            if should_log:
                audit_logger.error(
                    "HTTP request failed",
                    extra={
                        "audit": True,
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "client_ip": client_ip,
                        "duration_ms": round(duration * 1000, 2),
                        "error": str(e),
                    },
                )
            raise

        duration = time.time() - start_time

        if should_log:
            audit_logger.info(
                "HTTP response",
                extra={
                    "audit": True,
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "client_ip": client_ip,
                    "duration_ms": round(duration * 1000, 2),
                },
            )

        # Add request ID to response headers for tracing
        response.headers["X-Request-ID"] = request_id
        return response


def log_security_event(
    event_type: str,
    user_id: Optional[str] = None,
    ip: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
    severity: str = "info",
) -> None:
    """
    Log a security-relevant event with structured data.
    
    Args:
        event_type: Type of event (e.g., "login_success", "login_failed", "auth_bypass_attempt")
        user_id: User ID if available
        ip: Client IP address
        details: Additional event-specific details
        severity: Log level (info, warning, error, critical)
    """
    log_data = {
        "audit": True,
        "security_event": True,
        "event_type": event_type,
        "request_id": get_request_id(),
        "user_id": user_id,
        "ip": ip,
        "details": details or {},
        "severity": severity,
    }

    log_method = getattr(audit_logger, severity.lower(), audit_logger.info)
    log_method(f"Security event: {event_type}", extra=log_data)


def log_auth_event(
    event: str,
    user_id: str,
    ip: str,
    success: bool,
    details: Optional[dict[str, Any]] = None,
) -> None:
    """Log authentication-related events."""
    log_security_event(
        event_type=f"auth_{event}",
        user_id=user_id,
        ip=ip,
        details={"success": success, **(details or {})},
        severity="info" if success else "warning",
    )


def log_authorization_event(
    event: str,
    user_id: str,
    ip: str,
    resource: str,
    action: str,
    allowed: bool,
    details: Optional[dict[str, Any]] = None,
) -> None:
    """Log authorization (permission) decisions."""
    log_security_event(
        event_type=f"authz_{event}",
        user_id=user_id,
        ip=ip,
        details={
            "resource": resource,
            "action": action,
            "allowed": allowed,
            **(details or {}),
        },
        severity="info" if allowed else "warning",
    )


def log_rate_limit_event(
    user_id: Optional[str],
    ip: str,
    endpoint: str,
    limit: str,
) -> None:
    """Log rate limit exceeded events."""
    log_security_event(
        event_type="rate_limit_exceeded",
        user_id=user_id,
        ip=ip,
        details={"endpoint": endpoint, "limit": limit},
        severity="warning",
    )


def log_websocket_event(
    event: str,
    game_id: str,
    user_id: str,
    ip: str,
    details: Optional[dict[str, Any]] = None,
) -> None:
    """Log WebSocket connection events."""
    log_security_event(
        event_type=f"ws_{event}",
        user_id=user_id,
        ip=ip,
        details={"game_id": game_id, **(details or {})},
        severity="info",
    )


class AuditLogFormatter(logging.Formatter):
    """Custom formatter that properly handles extra fields."""
    
    def format(self, record: logging.LogRecord) -> str:
        # Collect standard fields
        log_dict = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields (skip standard logging fields)
        standard_fields = {
            "name", "msg", "args", "created", "filename", "funcName",
            "levelname", "levelno", "lineno", "module", "msecs",
            "message", "pathname", "process", "processName", "relativeCreated",
            "thread", "threadName", "exc_info", "exc_text", "stack_info",
            "asctime"
        }
        
        for key, value in record.__dict__.items():
            if key not in standard_fields:
                log_dict[key] = value
        
        return json.dumps(log_dict, ensure_ascii=False, default=str)


def configure_audit_logging(log_level: str = "INFO", json_format: bool = False) -> None:
    """Configure audit loggers with appropriate handlers."""
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    audit_logger.setLevel(level)
    logger.setLevel(level)

    if not audit_logger.handlers:
        handler = logging.StreamHandler()
        if json_format:
            formatter = AuditLogFormatter()
        else:
            # Human-readable format - just use standard format without extra
            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
            )
        handler.setFormatter(formatter)
        audit_logger.addHandler(handler)
        audit_logger.propagate = False

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False