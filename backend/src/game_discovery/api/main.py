import threading
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
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
from game_discovery.catalog.contracts import AppId, DiscoverRequest, DiscoverResponse, Game, Recommendation, StrictModel
from game_discovery.catalog.contracts import DiscoveryCapabilities
from game_discovery.catalog.repository import CatalogFailure, CatalogRepository, Facets, GamePage, ResolvedGames
from game_discovery.catalog.analytics import AnalyticsResponse
from game_discovery.retrieval.query import QueryEncoder, load_query_encoder
from game_discovery.ai.interpretation import experience_uncertainty, local_patch, resolve_criteria
from game_discovery.ai.provider import AIFailure, Assistant, ClientThrottle, DatabaseBudget, GroqAssistant
from game_discovery.ai.chat import ChatModel, ChatRequest, ChatResponse, respond as chat_reply
from game_discovery.api.errors import ApiError, ai_error_code, error_response
from game_discovery.ai.conversation_store import Archive, ConversationStore
from game_discovery.ai.dialogue import DialogueModel
from game_discovery.api.conversation_routes import register_conversations

T = TypeVar("T")


class ResolveRequest(StrictModel):
    app_ids: list[AppId] = Field(max_length=200)


class CatalogStatus(BaseModel):
    state: Literal["ready", "uninitialized"]
    catalog_version: str | None
    game_count: int
    region: Literal["US"] = "US"
    currency: Literal["USD"] = "USD"
    source_observed_at: datetime | None = None
    semantic_query_matching: bool = False
    semantic_catalog_version: str | None = None
    llm_enabled: bool = False


class LiveStatus(BaseModel):
    status: Literal["alive"] = "alive"


class ReadyStatus(BaseModel):
    status: Literal["ready"] = "ready"
    catalog_version: str


def create_app(settings: Settings | None = None, catalog_probe: Callable[[], CatalogReadiness] | None = None,
               repository: CatalogRepository | None = None, query_encoder: QueryEncoder | None = None,
               assistant: Assistant | None = None, chat_model: ChatModel | None = None,
               conversation_store: Archive | None = None, dialogue_model: DialogueModel | None = None) -> FastAPI:
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
    if assistant is None and settings.ai_enabled and settings.groq_api_key.get_secret_value() and engine is not None:
        assistant = GroqAssistant(settings, DatabaseBudget(engine, settings.ai_daily_calls, settings.ai_daily_tokens))
    if chat_model is None and isinstance(assistant, GroqAssistant):
        chat_model = assistant
    if dialogue_model is None and isinstance(assistant, GroqAssistant):
        dialogue_model = assistant
    if conversation_store is None and engine is not None:
        conversation_store = ConversationStore(engine)
    chat_slots = threading.BoundedSemaphore(1)
    chat_throttle = ClientThrottle()
    throttle = ClientThrottle()
    if query_encoder is None:
        try:
            query_encoder = load_query_encoder(settings.query_tokenizer_path, settings.query_model_path,
                                               settings.query_artifact_path)
        except Exception:
            # Optional local model load failure must not disable seed/filter discovery.
            # Do not log local paths, catalog text or environment values.
            query_encoder = None

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        if engine is not None:
            engine.dispose()

    app = FastAPI(title="Game Discovery API", version="0.1.0", lifespan=lifespan,
                  responses={422: {'model': ApiError}, 500: {'model': ApiError}})
    app.add_middleware(CORSMiddleware, allow_origins=list(settings.allowed_origins),
                       allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])

    @app.exception_handler(RequestValidationError)
    async def invalid_input(request: Request, error: RequestValidationError) -> JSONResponse:
        errors = error.errors()
        code = 'invalid_input'
        field: Literal['message', 'price', 'request'] = 'request'
        if request.url.path in {'/api/v1/chat', '/api/v2/assistant'}:
            if any(item['loc'] == ('body', 'message') and item['type'] == 'string_too_long' for item in errors):
                code, field = 'chat_message_too_long', 'message'
            elif any('version' in item['loc'] for item in errors):
                code = 'chat_incompatible'
            elif any('messages' in item['loc'] and item['type'] == 'too_long' for item in errors):
                code = 'chat_context_limit'
            else:
                field = 'message'
        elif any(item['type'] == 'value_error' and 'price' in str(item.get('ctx', {}).get('error', '')).lower() for item in errors):
            code, field = 'invalid_price_range', 'price'
        return error_response(request.state.request_id, code, field=field)

    @app.exception_handler(Exception)
    async def unexpected(request: Request, _: Exception) -> JSONResponse:
        return error_response(getattr(request.state, 'request_id', str(uuid4())), 'unexpected_error')

    @app.middleware("http")
    async def request_identity(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        request.state.request_id = str(uuid4())
        try:
            response = await call_next(request)
        except Exception:
            # Keep raw driver/provider payloads out of server error tracebacks too.
            response = error_response(request.state.request_id, 'unexpected_error')
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
        return error_response(request.state.request_id, code)

    def catalog_operation(request: Request, operation: Callable[[CatalogRepository], T]) -> T | JSONResponse:
        if repository is None:
            return unavailable(request, "database_unconfigured", False)
        if not slots.acquire(blocking=False):
            return unavailable(request, "database_busy", True)
        try:
            return operation(repository)
        except CatalogFailure as error:
            if error.code == "unknown_favorite":
                return error_response(request.state.request_id, error.code)
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
                              game_count=catalog.game_count, source_observed_at=catalog.observed_at,
                              semantic_query_matching=query_encoder is not None and query_encoder.catalog_version == catalog.version,
                              semantic_catalog_version=query_encoder.catalog_version if query_encoder is not None else None,
                              llm_enabled=assistant is not None)

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
            return error_response(request.state.request_id, 'game_not_found')
        return result.items[0]

    @app.get("/api/v1/facets", response_model=Facets, responses={503: {"model": ApiError}})
    def facets(request: Request) -> Facets | JSONResponse:
        return catalog_operation(request, lambda repo: repo.facets())

    @app.get('/api/v1/analytics', response_model=AnalyticsResponse, responses={503: {'model': ApiError}})
    def analytics(request: Request) -> AnalyticsResponse | JSONResponse:
        response = catalog_operation(request, lambda repo: repo.analytics())
        # Snapshot identity belongs to this response; never reuse an aggregate across activation.
        if isinstance(response, AnalyticsResponse):
            return JSONResponse(response.model_dump(mode='json'), headers={'Cache-Control': 'no-store'})
        return response

    @app.post("/api/v1/discover", response_model=DiscoverResponse, responses={503: {"model": ApiError}})
    def discover(request: Request, body: DiscoverRequest) -> DiscoverResponse | JSONResponse:
        started = time.perf_counter()
        query = body.ranking_text()
        patch, unresolved = local_patch(body.query)
        # Retain uncertainty for earlier subjective intent too.
        previous_uncertainty = experience_uncertainty(query)
        unresolved = list(dict.fromkeys(unresolved + previous_uncertainty))
        degraded: list[str] = []
        capabilities = DiscoveryCapabilities()
        use_ai = assistant is not None and bool(query) and throttle.allow(request.client.host if request.client else "unknown")
        if use_ai and assistant is not None and body.query.strip() and body.resolution is None:
            try:
                model_patch = assistant.interpret(body.query, body.effective_filters())
                # Clear local recognition wins over a model's alternative parsing.
                patch = type(patch).model_validate({**model_patch.model_dump(exclude_unset=True), **patch.model_dump(exclude_unset=True)})
                capabilities.ai_interpretation = True
            except (AIFailure, ValueError):
                use_ai = False
                degraded.append("AI interpretation is unavailable or its output could not be validated. Conservative text interpretation and explicit controls remain active.")
        elif query and assistant is None:
            degraded.append("AI assistance is disabled. Conservative text interpretation, available text matching and catalog-derived explanations remain active.")
        elif query and not use_ai:
            degraded.append("AI assistance is temporarily limited. Core discovery remains available.")
        effective, conflicts, proposed, criterion_uncertainty = resolve_criteria(body, patch)
        unresolved.extend(criterion_uncertainty)
        ranked_request = body.model_copy(update={"query": query, "filters": effective})
        core_started = time.perf_counter()
        interpretation_ms = round((core_started - started) * 1000, 2)
        query_vector = None
        if query:
            if query_encoder is not None:
                try:
                    query_vector = query_encoder(query)
                except Exception:
                    query_vector = None
            if query_vector is None:
                degraded.append("Semantic text matching is unavailable; using lexical text matching and any favorites.")

        def run_discovery(repo: CatalogRepository) -> tuple[str, list[Recommendation]]:
            if query_vector is None or query_encoder is None:
                return repo.discover(ranked_request)
            try:
                return repo.discover(ranked_request, query_vector=query_vector, encoder_version=query_encoder.catalog_version)
            except CatalogFailure as error:
                if error.code != "query_artifact_mismatch":
                    raise
                degraded.append("Query encoder does not match the active catalog; using lexical text matching and any favorites.")
                return repo.discover(ranked_request)

        result = catalog_operation(request, run_discovery)
        if isinstance(result, JSONResponse):
            return result
        version, results = result
        core_ms = round((time.perf_counter() - core_started) * 1000, 2)
        explanation_started = time.perf_counter()
        capabilities.semantic_query_matching = query_vector is not None and query_encoder is not None and query_encoder.catalog_version == version
        if use_ai and assistant is not None and results and not conflicts:
            try:
                results = assistant.explain(results)
                capabilities.ai_explanations = True
            except (AIFailure, ValueError):
                degraded.append("AI explanations are unavailable or could not be grounded. Catalog-derived explanations are shown instead.")
        summary = ("Your text conflicts with existing controls. Existing limits were kept; choose whether to apply the proposed changes."
                   if conflicts else "Kept your controls. Conflicting text changes were not applied. Experience preferences remain soft signals."
                   if body.resolution == "controls" else "Applied your chosen text changes. Other active criteria were retained; experience preferences remain soft signals."
                   if body.resolution == "text" else "Your active criteria were retained, with any unambiguous text changes applied. Experience preferences remain soft signals; inspect the catalog evidence and tradeoffs.")
        return DiscoverResponse(request_id=request.state.request_id, catalog_version=version,
            effective_criteria=effective, results=results,
            ranking_version="hybrid-text-v1" if query else "seed-feedback-v1",
            unresolved_preferences=list(dict.fromkeys(unresolved)), degraded_reasons=degraded,
            conflicts=conflicts, proposed_criteria=proposed, effective_query=query, assistant_message=summary,
            capabilities=capabilities,
            suggested_refinements=[] if results else ["Try a higher recorded-price limit, fewer required modes, or another platform."],
            timings_ms={"core": core_ms, "interpretation": interpretation_ms,
                        "explanations": round((time.perf_counter() - explanation_started) * 1000, 2),
                         "total": round((time.perf_counter() - started) * 1000, 2)})

    @app.post("/api/v1/chat", response_model=ChatResponse, responses={status: {'model': ApiError} for status in (409, 422, 429, 502, 503, 504)})
    def chat(request: Request, body: ChatRequest) -> ChatResponse | JSONResponse:
        if chat_model is None:
            return error_response(request.state.request_id, 'chat_unconfigured')
        if repository is None:
            return unavailable(request, "database_unconfigured", False)
        if not chat_slots.acquire(blocking=False):
            return error_response(request.state.request_id, 'chat_busy')
        try:
            peer = request.client.host if request.client else 'unknown'
            if not chat_throttle.allow(peer):
                return error_response(request.state.request_id, 'chat_rate_limited',
                    retry_at=datetime.now(UTC) + timedelta(seconds=chat_throttle.remaining(peer)))
            # No database connection is held across provider calls. Main-discovery
            # request slots are independent; the existing pool still bounds SQL.
            return chat_reply(body, chat_model, repository, query_encoder, request.state.request_id)
        except AIFailure as error:
            return error_response(request.state.request_id, ai_error_code(error.code), retry_at=error.retry_at)
        except ValueError:
            return error_response(request.state.request_id, 'chat_invalid_answer')
        except CatalogFailure as error:
            return unavailable(request, error.code, False)
        except SQLAlchemyError:
            return unavailable(request, "database_unavailable", True)
        finally:
            chat_slots.release()

    register_conversations(app, conversation_store, dialogue_model, repository, query_encoder, chat_slots, chat_throttle)
    return app


app = create_app()
