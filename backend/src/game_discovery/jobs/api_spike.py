"""Loopback-only M0 API resource experiment; not a deployed discovery server."""

import os
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


class EncodeInput(BaseModel):
    text: str = Field(max_length=16000)


def load_encoder():
    from game_discovery.retrieval.encoder import OnnxEncoder

    return OnnxEncoder(Path(os.environ["M0_TOKENIZER_PATH"]), Path(os.environ["M0_MODEL_PATH"]))


def probe_database() -> bool:
    from dotenv import dotenv_values

    from game_discovery.jobs.environment_check import read_only_db_check

    config = dotenv_values(os.environ["M0_ENV_FILE"], interpolate=False)
    return read_only_db_check(config.get("DATABASE_URL") or "")["status"] == "ok"


def create_app(encoder_factory=load_encoder, database_probe=probe_database):
    @asynccontextmanager
    async def lifespan(app):
        try:
            app.state.encoder = encoder_factory()
        except (OSError, ValueError, KeyError):
            app.state.encoder = None
        app.state.inference_slot = threading.BoundedSemaphore(1)
        yield
        app.state.encoder = None

    app = FastAPI(title="M0 local resource spike", lifespan=lifespan)

    @app.get("/health/live")
    def live():
        return {"status": "alive", "purpose": "m0_resource_experiment"}

    @app.get("/health/ready")
    def ready():
        # The spike is not an activated discovery application even with a healthy DB.
        return JSONResponse(status_code=503, content={
            "code": "catalog_not_initialized", "database_available": database_probe(),
            "encoder_available": app.state.encoder is not None, "catalog_active": False,
            "ai_enabled": False,
        })

    @app.post("/spike/encode")
    def encode(body: EncodeInput):
        if app.state.encoder is None:
            return JSONResponse(status_code=503, content={"code": "encoder_unavailable"})
        if not app.state.inference_slot.acquire(blocking=False):
            return JSONResponse(status_code=429, content={"code": "inference_busy"})
        try:
            vector = app.state.encoder.encode([body.text])[0]
            return {"dimensions": 384, "embedding": vector.tolist()}
        finally:
            app.state.inference_slot.release()

    return app


app = create_app()
