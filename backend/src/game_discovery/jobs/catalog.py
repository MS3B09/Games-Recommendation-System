"""Small sequential catalog jobs, with checked snapshots and atomic publication."""

import hashlib
import html
import json
import re
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import Request, urlopen

from dotenv import dotenv_values
from sqlalchemy import create_engine, text

from game_discovery.catalog.contracts import (
    MODEL_ID, MODEL_REVISION, Embedding, Evidence, Game, Price, Source, digest, semantic_hash, semantic_text,
)
from game_discovery.catalog.eligibility import classify_appdetails
from game_discovery.core.database_url import normalize_db_url

MODE_IDS = {2: "single-player", 1: "multiplayer", 38: "online-co-op", 39: "local-co-op"}


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def plain_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]*>", " ", value))).strip()


def normalize_payload(app_id: int, payload: dict, source: Source) -> Game:
    envelope = payload.get(str(app_id), {})
    data = envelope.get("data", {})
    if envelope.get("success") is not True or data.get("steam_appid") != app_id:
        raise ValueError("Unverified app identity")
    classification = classify_appdetails(data)
    title = plain_text(data.get("name", ""))
    description = plain_text(data.get("short_description", ""))[:16000]
    genres = sorted({plain_text(item["description"]).casefold() for item in data.get("genres", [])
                     if isinstance(item, dict) and isinstance(item.get("description"), str)})
    modes = sorted({MODE_IDS[item["id"]] for item in data.get("categories", [])
                    if isinstance(item, dict) and item.get("id") in MODE_IDS})
    platforms = {name: value if type(value) is bool else None
                 for name in ("windows", "mac", "linux")
                 for value in [data.get("platforms", {}).get(name)]}
    free = data.get("is_free") if type(data.get("is_free")) is bool else None
    evidence = []

    def add(field: str, value: str | int | bool | list[str]) -> str:
        evidence_id = f"{app_id}:{field}"
        evidence.append(Evidence(id=evidence_id, field=field, value=value, source=source))
        return evidence_id

    add("title", title)
    add("description", description)
    add("genres", genres)
    add("modes", modes)
    add("eligibility", classification["reason"])
    if classification["early_access"] is not None:
        add("early_access", classification["early_access"])
    for platform, supported in platforms.items():
        if supported is not None:
            add(f"platform:{platform}", supported)
    if free is not None:
        add("free_to_play", free)
    raw_price = data.get("price_overview", {})
    amount = raw_price.get("final")
    price = None
    if raw_price.get("currency") == "USD" and type(amount) is int and amount >= 0:
        price = Price(amount_cents=amount, observed_at=source.collected_at, evidence_id=add("price_cents", amount))
    elif free is True:
        price = Price(amount_cents=0, observed_at=source.collected_at, evidence_id=f"{app_id}:free_to_play")
    artwork = data.get("header_image")
    game = Game.model_construct(
        app_id=app_id, title=title, description=description,
        store_url=f"https://store.steampowered.com/app/{app_id}/?cc=us",
        artwork_url=artwork if isinstance(artwork, str) and artwork.startswith("https://") else None,
        eligibility=classification["status"], eligibility_reason=classification["reason"],
        early_access=classification["early_access"], platforms=platforms, genres=genres, tags=[], modes=modes,
        free_to_play=free, price=price, observed_at=source.collected_at, evidence=evidence, semantic_hash="",
    )
    game.semantic_hash = semantic_hash(game)
    return Game.model_validate(game.model_dump())


def collect(run_dir: Path, app_ids: list[int], resume: bool) -> dict:
    if not 1 <= len(app_ids) <= 100 or any(value <= 0 for value in app_ids) or len(set(app_ids)) != len(app_ids):
        raise ValueError("Collection requires 1–100 distinct positive IDs")
    path = run_dir / "collection.json"
    report = {"schema_version": 1, "region": "US", "app_ids": app_ids, "observations": []}
    if path.exists():
        if not resume:
            raise ValueError("Existing run requires --resume")
        report = json.loads(path.read_text(encoding="utf-8"))
        if report["app_ids"] != app_ids:
            raise ValueError("Resume identity set mismatch")
    complete = {item["app_id"] for item in report["observations"] if item.get("source")}
    for app_id in app_ids:
        if app_id in complete:
            continue
        url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&cc=us&l=english"
        collected_at = datetime.now(UTC)
        try:
            with urlopen(Request(url, headers={"User-Agent": "GameDiscoveryCatalog/0.1"}), timeout=20) as response:
                body = response.read(2 * 1024 * 1024 + 1)
                if response.status != 200 or len(body) > 2 * 1024 * 1024:
                    raise ValueError("Invalid bounded source response")
            payload = json.loads(body)
            source = Source(url=url, collected_at=collected_at, sha256=hashlib.sha256(body).hexdigest())
            normalize_payload(app_id, payload, source)
            snapshot = run_dir / f"{app_id}-appdetails.json"
            snapshot.parent.mkdir(parents=True, exist_ok=True)
            snapshot.write_bytes(body)
            observation = {"app_id": app_id, "snapshot": snapshot.name, "source": source.model_dump(mode="json")}
        except Exception as error:
            observation = {"app_id": app_id, "error_type": type(error).__name__}
        report["observations"] = [item for item in report["observations"] if item["app_id"] != app_id] + [observation]
        write_json(path, report)
        time.sleep(2)
    return report


def normalize(run_dir: Path) -> dict:
    report = json.loads((run_dir / "collection.json").read_text(encoding="utf-8"))
    games = []
    quarantine = []
    for item in report["observations"]:
        if not item.get("source"):
            quarantine.append({"app_id": item["app_id"], "reason": "collection_failed"})
            continue
        source = Source.model_validate(item["source"])
        body = (run_dir / item["snapshot"]).read_bytes()
        if hashlib.sha256(body).hexdigest() != source.sha256:
            raise ValueError("Raw snapshot hash mismatch")
        game = normalize_payload(item["app_id"], json.loads(body), source)
        if game.eligibility != "eligible" or not game.description:
            quarantine.append({"app_id": game.app_id, "reason": game.eligibility_reason if game.description else "missing_description"})
            continue
        games.append(game.model_dump(mode="json"))
    games.sort(key=lambda game: game["app_id"])
    if not games:
        raise ValueError("No eligible games")
    write_json(run_dir / "games.json", games)
    result = {"schema_version": 1, "games": len(games), "requested": len(report["app_ids"]),
              "quarantine": quarantine, "games_sha256": digest(games), "model_id": MODEL_ID,
              "model_revision": MODEL_REVISION, "dimensions": 384, "semantic_text_version": "title-terms-description-v1"}
    write_json(run_dir / "normalized.json", result)
    return result


def load_games(run_dir: Path) -> tuple[list[Game], dict]:
    manifest = json.loads((run_dir / "normalized.json").read_text(encoding="utf-8"))
    documents = json.loads((run_dir / "games.json").read_text(encoding="utf-8"))
    if digest(documents) != manifest["games_sha256"] or len(documents) != manifest["games"]:
        raise ValueError("Normalized artifact mismatch")
    games = [Game.model_validate(document) for document in documents]
    if len({game.app_id for game in games}) != len(games) or any(game.eligibility != "eligible" for game in games):
        raise ValueError("Invalid publication identities or eligibility")
    return games, manifest


def embed(run_dir: Path, cache_dir: Path, batch_size: int, resume: bool) -> dict:
    from huggingface_hub import hf_hub_download
    from game_discovery.retrieval.encoder import OnnxEncoder

    if not 1 <= batch_size <= 16:
        raise ValueError("Invalid embedding settings")
    games, manifest = load_games(run_dir)
    if (manifest.get("model_id"), manifest.get("model_revision"), manifest.get("dimensions")) != (MODEL_ID, MODEL_REVISION, 384):
        raise ValueError("Incompatible catalog model manifest")
    cache_dir.mkdir(parents=True, exist_ok=True)
    tokenizer = Path(hf_hub_download(MODEL_ID, "tokenizer.json", revision=MODEL_REVISION, cache_dir=cache_dir))
    model = Path(hf_hub_download(MODEL_ID, "onnx/model.onnx", revision=MODEL_REVISION, cache_dir=cache_dir))
    representation = {"model_id": MODEL_ID, "model_revision": MODEL_REVISION,
                      "tokenizer_sha256": hashlib.sha256(tokenizer.read_bytes()).hexdigest(),
                      "model_sha256": hashlib.sha256(model.read_bytes()).hexdigest()}
    encoder = OnnxEncoder(tokenizer, model)
    checkpoint = run_dir / "embeddings.json"
    settings_path = run_dir / "embedding-settings.json"
    reusable = resume and checkpoint.exists() and settings_path.exists()
    if reusable and json.loads(settings_path.read_text(encoding="utf-8")) != representation:
        raise ValueError("Checkpoint model representation mismatch")
    vectors = json.loads(checkpoint.read_text(encoding="utf-8")) if reusable else []
    write_json(settings_path, representation)
    expected = {game.app_id: game.semantic_hash for game in games}
    vectors = [Embedding.model_validate(item).model_dump() for item in vectors
               if expected.get(item["app_id"]) == item["semantic_hash"]]
    if len({item["app_id"] for item in vectors}) != len(vectors):
        raise ValueError("Duplicate embedding checkpoint")
    done = {item["app_id"] for item in vectors}
    pending = [game for game in games if game.app_id not in done]
    started = time.perf_counter()
    for offset in range(0, len(pending), batch_size):
        batch = pending[offset:offset + batch_size]
        encoded = encoder.encode([semantic_text(game) for game in batch])
        vectors.extend(Embedding(app_id=game.app_id, semantic_hash=game.semantic_hash, vector=vector.tolist()).model_dump()
                       for game, vector in zip(batch, encoded, strict=True))
        vectors.sort(key=lambda item: item["app_id"])
        write_json(checkpoint, vectors)
    artifact = {**manifest, "embeddings_sha256": digest(vectors), "encoder": "float-onnx-cpu-parity-verified",
                "tokenizer_sha256": hashlib.sha256(tokenizer.read_bytes()).hexdigest(),
                "model_sha256": hashlib.sha256(model.read_bytes()).hexdigest()}
    artifact["version"] = "m2-" + digest(artifact)[:24]
    write_json(run_dir / "artifact.json", artifact)
    return {"version": artifact["version"], "embedded": len(pending), "reused": len(done),
            "elapsed_seconds": round(time.perf_counter() - started, 3)}


def validated_artifact(run_dir: Path) -> tuple[list[Game], list[Embedding], dict]:
    games, manifest = load_games(run_dir)
    artifact = json.loads((run_dir / "artifact.json").read_text(encoding="utf-8"))
    if (artifact.get("model_id"), artifact.get("model_revision"), artifact.get("dimensions")) != (MODEL_ID, MODEL_REVISION, 384):
        raise ValueError("Incompatible artifact model")
    vectors = json.loads((run_dir / "embeddings.json").read_text(encoding="utf-8"))
    if any(artifact.get(key) != value for key, value in manifest.items()):
        raise ValueError("Artifact manifest mismatch")
    unsigned = {key: value for key, value in artifact.items() if key != "version"}
    if artifact["version"] != "m2-" + digest(unsigned)[:24] or artifact["embeddings_sha256"] != digest(vectors):
        raise ValueError("Artifact checksum mismatch")
    embeddings = [Embedding.model_validate(item) for item in vectors]
    if {game.app_id: game.semantic_hash for game in games} != {item.app_id: item.semantic_hash for item in embeddings}:
        raise ValueError("Incomplete or incompatible embeddings")
    if len(embeddings) != len(games):
        raise ValueError("Duplicate embeddings")
    return games, embeddings, artifact


def publish(run_dir: Path, env_file: Path, activate: bool) -> dict:
    games, embeddings, artifact = validated_artifact(run_dir)
    raw_url = dotenv_values(env_file, interpolate=False).get("MIGRATION_DATABASE_URL")
    if not raw_url:
        raise ValueError("Configure MIGRATION_DATABASE_URL in the local env file")
    from sqlalchemy.engine import make_url
    url = make_url(normalize_db_url(raw_url)).set(drivername="postgresql+psycopg")
    engine = create_engine(url, hide_parameters=True, connect_args={"prepare_threshold": None, "connect_timeout": 10})
    version = artifact["version"]
    vectors = {item.app_id: item for item in embeddings}
    try:
        with engine.begin() as connection:
            connection.execute(text("SET LOCAL statement_timeout = '180s'"))
            connection.execute(text("SET LOCAL lock_timeout = '5s'"))
            connection.execute(text("select pg_advisory_xact_lock(7349201)"))
            existing = connection.execute(text("select game_count from discovery.catalog_versions where version=:v"), {"v": version}).scalar()
            if existing is None:
                connection.execute(text("""insert into discovery.catalog_versions
                    (version,game_count,model_id,model_revision,dimensions,region,currency,source_observed_at)
                    values (:v,:n,:model,:revision,384,'US','USD',:observed)"""),
                    {"v": version, "n": len(games), "model": MODEL_ID, "revision": MODEL_REVISION,
                     "observed": min(game.observed_at for game in games)})
                for game in games:
                    params = {"v": version, "id": game.app_id}
                    connection.execute(text("""insert into discovery.games
                        (version,app_id,title,normalized_title,description,eligibility,semantic_hash,document)
                        values (:v,:id,:title,:normalized,:description,:eligibility,:hash,cast(:doc as jsonb))"""),
                        {**params, "title": game.title, "normalized": game.title.casefold(), "description": game.description,
                         "eligibility": game.eligibility, "hash": game.semantic_hash, "doc": game.model_dump_json()})
                    for platform, supported in game.platforms.items():
                        connection.execute(text("insert into discovery.game_platforms values (:v,:id,:platform,:supported)"),
                                           {**params, "platform": platform, "supported": supported})
                    for kind, terms in (("genre", game.genres), ("tag", game.tags), ("mode", game.modes)):
                        for term in sorted(set(terms)):
                            connection.execute(text("insert into discovery.game_terms values (:v,:id,:kind,:term)"),
                                               {**params, "kind": kind, "term": term})
                    connection.execute(text("insert into discovery.game_prices values (:v,:id,:amount,:free,'US','USD',:observed)"),
                                       {**params, "amount": game.price.amount_cents if game.price else None,
                                        "free": game.free_to_play, "observed": game.price.observed_at if game.price else None})
                    connection.execute(text("insert into discovery.game_embeddings values (:v,:id,:hash,cast(:vector as extensions.vector))"),
                                       {**params, "hash": game.semantic_hash, "vector": json.dumps(vectors[game.app_id].vector)})
            counts = connection.execute(text("""select
                (select count(*) from discovery.games where version=:v),
                (select count(*) from discovery.game_embeddings where version=:v)"""), {"v": version}).one()
            if tuple(counts) != (len(games), len(games)):
                raise ValueError("Staged database counts mismatch")
            stored = connection.execute(text("select document from discovery.games where version=:v order by app_id"), {"v": version})
            if [row[0] for row in stored] != [game.model_dump(mode="json") for game in games]:
                raise ValueError("Staged database documents mismatch")
            metadata = connection.execute(text("select model_id,model_revision,dimensions from discovery.catalog_versions where version=:v"), {"v": version}).one()
            if tuple(metadata) != (MODEL_ID, MODEL_REVISION, 384):
                raise ValueError("Staged database model mismatch")
            stored_vectors = connection.execute(text("select app_id,semantic_hash,cast(embedding as text) from discovery.game_embeddings where version=:v"), {"v": version})
            for app_id, content_hash, vector in stored_vectors:
                values = json.loads(vector)
                expected = vectors[app_id]
                if content_hash != expected.semantic_hash or any(abs(a - b) > 1e-6 for a, b in zip(values, expected.vector, strict=True)):
                    raise ValueError("Staged database embeddings mismatch")
            stored_platforms = list(connection.execute(text("select app_id,platform,supported from discovery.game_platforms where version=:v order by app_id,platform"), {"v": version}))
            expected_platforms = sorted((game.app_id, platform, supported) for game in games for platform, supported in game.platforms.items())
            if [tuple(row) for row in stored_platforms] != expected_platforms:
                raise ValueError("Staged database platforms mismatch")
            stored_terms = list(connection.execute(text("select app_id,kind,term from discovery.game_terms where version=:v order by app_id,kind,term"), {"v": version}))
            expected_terms = sorted((game.app_id, kind, term) for game in games
                for kind, terms in (("genre", game.genres), ("tag", game.tags), ("mode", game.modes)) for term in set(terms))
            if [tuple(row) for row in stored_terms] != expected_terms:
                raise ValueError("Staged database taxonomy mismatch")
            stored_prices = list(connection.execute(text("select app_id,amount_cents,free_to_play,region,currency,observed_at from discovery.game_prices where version=:v order by app_id"), {"v": version}))
            expected_prices = [(game.app_id, game.price.amount_cents if game.price else None, game.free_to_play,
                "US", "USD", game.price.observed_at if game.price else None) for game in games]
            if [tuple(row) for row in stored_prices] != expected_prices:
                raise ValueError("Staged database prices mismatch")
            if activate:
                # Lock makes competing imports/publications serialize; old snapshot stays usable for rollback.
                previous = connection.execute(text("select version from discovery.catalog_versions where active")).scalar()
                connection.execute(text("update discovery.catalog_versions set active=false where active"))
                connection.execute(text("update discovery.catalog_versions set active=true,activated_at=now() where version=:v"), {"v": version})
            size = connection.execute(text("select pg_database_size(current_database())")).scalar_one()
            if size >= 350 * 1024 * 1024:
                raise ValueError("Database storage budget exceeded")
            active = connection.execute(text("select active from discovery.catalog_versions where version=:v"), {"v": version}).scalar_one()
        result = {"version": version, "games": len(games), "reused": existing is not None,
                  "active": active, "activation_requested": activate, "database_bytes": size}
        if activate:
            result["previous_version"] = previous
        write_json(run_dir / ("activation-report.json" if activate else "import-report.json"), result)
        return result
    finally:
        engine.dispose()
