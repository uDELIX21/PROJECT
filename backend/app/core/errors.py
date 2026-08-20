"""Consistent error envelope (design §05). No stack traces leak to clients (BR-U07)."""
import uuid
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ApiError(Exception):
    status_code = 400
    default_code = "BAD_REQUEST"
    default_message = "Request could not be processed."

    def __init__(self, message: str | None = None, *, code: str | None = None,
                 status_code: int | None = None, details: Any = None):
        message = message or self.default_message
        super().__init__(message)
        self.message = message
        self.code = code or self.default_code
        if status_code is not None:
            self.status_code = status_code
        self.details = details


class UnauthorizedError(ApiError):
    status_code = 401
    default_code = "AUTH_REQUIRED"
    default_message = "Authentication required."


class ForbiddenError(ApiError):
    status_code = 403
    default_code = "FORBIDDEN"


class NotFoundError(ApiError):
    status_code = 404
    default_code = "NOT_FOUND"


class ConflictError(ApiError):
    status_code = 409
    default_code = "CONFLICT"


class LockedError(ApiError):
    status_code = 423
    default_code = "LOCKED"


class RateLimitedError(ApiError):
    status_code = 429
    default_code = "RATE_LIMITED"

    def __init__(self, message: str = "Too many requests.", retry_after: int = 60, **kw):
        super().__init__(message, **kw)
        self.retry_after = retry_after


def _envelope(code: str, message: str, request: Request, details: Any = None) -> dict:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or [],
            "request_id": getattr(request.state, "request_id", None),
        }
    }


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def api_error_handler(request: Request, exc: ApiError):
        headers = {}
        if isinstance(exc, RateLimitedError):
            headers["Retry-After"] = str(exc.retry_after)
        return JSONResponse(status_code=exc.status_code,
                            content=_envelope(exc.code, exc.message, request, exc.details),
                            headers=headers)

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        details = []
        for e in exc.errors():
            details.append({
                "field": ".".join(str(p) for p in e.get("loc", []) if p != "body"),
                "issue": e.get("type", "invalid"),
                "msg": e.get("msg"),
            })
        return JSONResponse(status_code=422,
                            content=_envelope("VALIDATION_FAILED",
                                              "Request validation failed.", request, details))

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception):
        # Log internally (with traceback); client gets a generic envelope.
        import logging
        logging.getLogger("sms").exception("unhandled error request_id=%s",
                                           getattr(request.state, "request_id", None))
        return JSONResponse(status_code=500,
                            content=_envelope("INTERNAL", "An unexpected error occurred.", request))


def new_request_id() -> str:
    return str(uuid.uuid4())
