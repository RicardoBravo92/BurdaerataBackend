from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import engine, init_db
from app.core.rate_limit import limiter
from app.core.security_headers import SecurityHeadersMiddleware
from app.core.request_size_limit import RequestSizeLimitMiddleware
from app.core.audit_log import AuditLogMiddleware, configure_audit_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )

    # Configure audit logging
    configure_audit_logging(
        log_level="DEBUG" if settings.debug else "INFO",
        json_format=not settings.debug,  # JSON in production
    )

    # Audit logging (add early to capture all requests)
    app.add_middleware(AuditLogMiddleware)

    # Request size limits (add early to reject large payloads before processing)
    app.add_middleware(RequestSizeLimitMiddleware)

    # Security headers (add first so they apply to all responses)
    app.add_middleware(SecurityHeadersMiddleware)

    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.authorized_parties,
        allow_credentials=settings.allow_credentials,
        allow_methods=settings.allowed_methods,
        allow_headers=settings.allowed_headers,
    )

    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}