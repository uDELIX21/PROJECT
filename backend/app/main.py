"""FastAPI application factory."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes import (appraisals, assessments, attendance, audit, auth,
                            classes, communications, curriculum, discipline, ecd,
                            enrollments, fees, grade_scales, imports, meta, parents, payments,
                            pickup, receipts, reports, students, sync, teachers, users)
from app.api.routes import settings as settings_routes
from app.core.config import get_settings
from app.core.db import get_engine
from app.core.errors import install_error_handlers, new_request_id

API_PREFIX = "/api/v1"


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.3.0",
                  docs_url="/api/docs" if settings.dev_mode else None,
                  openapi_url="/api/openapi.json" if settings.dev_mode else None)

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        request.state.request_id = new_request_id()
        response = await call_next(request)
        response.headers["X-Request-Id"] = request.state.request_id
        return response

    install_error_handlers(app)

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    @app.get("/healthz/ready")
    def ready():
        from sqlalchemy import text
        try:
            with get_engine().connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception:
            return JSONResponse(status_code=503,
                                content={"error": {"code": "DB_UNAVAILABLE",
                                                   "message": "Database is not reachable.",
                                                   "details": [], "request_id": None}})
        return {"status": "ready"}

    for module in (auth, users, students, parents, teachers, classes, enrollments,
                   settings_routes, audit, meta, curriculum, assessments, grade_scales,
                   attendance, ecd, reports, fees, payments, receipts, appraisals,
                   discipline, pickup, communications, sync, imports):
        app.include_router(module.router, prefix=API_PREFIX)

    return app


app = create_app()
