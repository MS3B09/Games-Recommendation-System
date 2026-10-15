import threading
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Literal, TypeVar
from uuid import uuid4

from fastapi import FastAPI, Path, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.exc import ArgumentError, SQLAlchemyError
from starlette.responses import Response

from game_discovery.core.settings import Settings
from game_discovery.db.engine import create_runtime_engine
from game_discovery.db.readiness import CatalogReadiness, probe_catalog
from game_discovery.catalog.contracts import AppId, DiscoverRequest, DiscoverResponse, Game, StrictModel
from game_discovery.catalog.repository import CatalogFailure, CatalogRepository, Facets, GamePage, ResolvedGames

T = TypeVar("T")


class ResolveRequest(StrictModel):
    app_ids: list[AppId] = Field(max_length=200)


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


def create_app(settings: Settings | None = None, catalog_probe: Callable[[], CatalogReadiness] | None = None,
               repository: CatalogRepository | None = None) -> FastAPI:
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
    repository = repository or (CatalogRepository(engine) if engine is not None else None)
    slots = threading.BoundedSemaphore(2)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        if engine is not None:
            engine.dispose()

    app = FastAPI(title="Game Discovery API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=list(settings.allowed_origins),
                       allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])

    @app.exception_handler(RequestValidationError)
    async def invalid_input(request: Request, _: RequestValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content=ApiError(
            code="invalid_input", message="Check the bounded request fields and filter values.",
            request_id=request.state.request_id, retryable=False).model_dump())

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

    def catalog_operation(request: Request, operation: Callable[[CatalogRepository], T]) -> T | JSONResponse:
        if repository is None:
            return unavailable(request, "database_unconfigured", False)
        if not slots.acquire(blocking=False):
            return unavailable(request, "database_busy", True)
        try:
            return operation(repository)
        except CatalogFailure as error:
            if error.code == "unknown_favorite":
                return JSONResponse(status_code=422, content=ApiError(
                    code=error.code, message="A favorite is not in the active catalog. Search and select it again.",
                    request_id=request.state.request_id, retryable=False).model_dump())
            return unavailable(request, error.code, False)
        except SQLAlchemyError:
            return unavailable(request, "database_unavailable", True)
        except ValueError:
            return unavailable(request, "catalog_integrity_error", False)
        finally:
            slots.release()

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

    @app.get("/api/v1/games", response_model=GamePage, responses={503: {"model": ApiError}})
    def games(request: Request, q: str = Query(default="", max_length=200),
              limit: int = Query(default=20, ge=1, le=50), offset: int = Query(default=0, ge=0, le=6000)) -> GamePage | JSONResponse:
        return catalog_operation(request, lambda repo: repo.search(q.strip(), limit, offset))

    @app.post("/api/v1/games/resolve", response_model=ResolvedGames, responses={503: {"model": ApiError}})
    def resolve(request: Request, body: ResolveRequest) -> ResolvedGames | JSONResponse:
        return catalog_operation(request, lambda repo: repo.resolve(body.app_ids))

    @app.get("/api/v1/games/{app_id}", response_model=Game, responses={404: {"model": ApiError}, 503: {"model": ApiError}})
    def detail(request: Request, app_id: int = Path(gt=0, le=2147483647)) -> Game | JSONResponse:
        result = catalog_operation(request, lambda repo: repo.resolve([app_id]))
        if isinstance(result, JSONResponse):
            return result
        if not result.items:
            return JSONResponse(status_code=404, content=ApiError(code="game_not_found", message="Game is not in the active catalog.",
                request_id=request.state.request_id, retryable=False).model_dump())
        return result.items[0]

    @app.get("/api/v1/facets", response_model=Facets, responses={503: {"model": ApiError}})
    def facets(request: Request) -> Facets | JSONResponse:
        return catalog_operation(request, lambda repo: repo.facets())

    @app.post("/api/v1/discover", response_model=DiscoverResponse, responses={503: {"model": ApiError}})
    def discover(request: Request, body: DiscoverRequest) -> DiscoverResponse | JSONResponse:
        started = time.perf_counter()
        result = catalog_operation(request, lambda repo: repo.discover(body))
        if isinstance(result, JSONResponse):
            return result
        version, results = result
        return DiscoverResponse(request_id=request.state.request_id, catalog_version=version,
            effective_criteria=body.filters, results=results,
            suggested_refinements=[] if results else ["Try a higher recorded-price limit, fewer required modes, or another platform."],
            timings_ms={"core": round((time.perf_counter() - started) * 1000, 2)})

    return app


app = create_app()
