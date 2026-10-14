import threading
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.exc import ArgumentError
from starlette.responses import Response

from game_discovery.core.settings import Settings
from game_discovery.db.engine import create_runtime_engine
from game_discovery.db.readiness import CatalogReadiness, probe_catalog


class ApiError(BaseModel):
    code: str
    message: str
    request_id: str
    retryable: bool


class CatalogStatus(BaseModel):
    state: Literal["ready", "uninitialized"]
    catalog_version: str | None
    game_count: int
    region: Literal["US"] = "US"
    currency: Literal["USD"] = "USD"
    source_observed_at: datetime | None = None
    semantic_query_matching: bool = False
    llm_enabled: bool = False


class LiveStatus(BaseModel):
    status: Literal["alive"] = "alive"


class ReadyStatus(BaseModel):
    status: Literal["ready"] = "ready"
    catalog_version: str


def create_app(settings: Settings | None = None, catalog_probe: Callable[[], CatalogReadiness] | None = None) -> FastAPI:
    settings = settings or Settings.from_environment()
    engine = None
    configuration_invalid = False
    if catalog_probe is None:
        try:
            engine = create_runtime_engine(settings.database_url)
        except (ValueError, ArgumentError):
            configuration_invalid = True

    def default_probe() -> CatalogReadiness:
        if configuration_invalid:
            return CatalogReadiness(error_code="database_configuration_invalid")
        return probe_catalog(settings.database_url, engine)

    probe = catalog_probe or default_probe
    slots = threading.BoundedSemaphore(2)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        if engine is not None:
            engine.dispose()

    app = FastAPI(title="Game Discovery API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=list(settings.allowed_origins),
                       allow_credentials=False, allow_methods=["GET"], allow_headers=["Content-Type"])

    @app.middleware("http")
    async def request_identity(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        request.state.request_id = str(uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    def current_catalog() -> CatalogReadiness:
        if not slots.acquire(blocking=False):
            return CatalogReadiness(error_code="database_busy", retryable=True)
        try:
            return probe()
        finally:
            slots.release()

    def unavailable(request: Request, code: str, retryable: bool) -> JSONResponse:
        messages = {
            "database_unconfigured": "Database configuration is not available.",
            "database_configuration_invalid": "Database configuration needs attention.",
            "database_role_misconfigured": "The runtime database role needs configuration.",
            "database_busy": "The service is busy. Try again shortly.",
            "database_unavailable": "The catalog database is temporarily unavailable.",
            "catalog_not_initialized": "The catalog has not been published yet.",
        }
        error = ApiError(code=code, message=messages.get(code, "The catalog is unavailable."),
                         request_id=request.state.request_id, retryable=retryable)
        return JSONResponse(status_code=503, content=error.model_dump())

    @app.get("/health/live", response_model=LiveStatus)
    def live() -> LiveStatus:
        return LiveStatus()

    @app.get("/health/ready", response_model=ReadyStatus, responses={503: {"model": ApiError}})
    def ready(request: Request) -> ReadyStatus | JSONResponse:
        catalog = current_catalog()
        if catalog.error_code:
            return unavailable(request, catalog.error_code, catalog.retryable)
        if catalog.version is None:
            return unavailable(request, "catalog_not_initialized", False)
        return ReadyStatus(catalog_version=catalog.version)

    @app.get("/api/v1/catalog/status", response_model=CatalogStatus, responses={503: {"model": ApiError}})
    def status(request: Request) -> CatalogStatus | JSONResponse:
        catalog = current_catalog()
        if catalog.error_code:
            return unavailable(request, catalog.error_code, catalog.retryable)
        return CatalogStatus(state="ready" if catalog.version else "uninitialized", catalog_version=catalog.version,
                             game_count=catalog.game_count, source_observed_at=catalog.observed_at)

    return app


app = create_app()
