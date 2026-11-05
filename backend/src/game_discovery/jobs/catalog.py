"""Small sequential catalog jobs, with checked snapshots and atomic publication."""

import hashlib
import html
import json
import re
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from dotenv import dotenv_values
from sqlalchemy import create_engine, text

from game_discovery.catalog.contracts import (
    MODEL_ID, MODEL_REVISION, DashboardMetadata, Embedding, Evidence, Game, Price, Source, digest, semantic_hash, semantic_text,
)
from game_discovery.catalog.eligibility import classify_appdetails
from game_discovery.catalog.metadata import normalize_metadata
from game_discovery.core.database_url import normalize_db_url
from game_discovery.jobs.probe import verified_review_summary
from game_discovery.retrieval.titles import normalize_title

MODE_IDS = {2: "single-player", 1: "multiplayer", 38: "online-co-op", 39: "local-co-op"}
MAX_COLLECTION_IDS = 2500  # Approved 2,000 eligible games plus a bounded replacement queue.
REVIEW_SCOPE = 'all-languages-all-purchases-offtopic-filtered-v1'


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


def source_payload(run_dir: Path, item: dict) -> tuple[dict, Source]:
    source = Source.model_validate(item['source'])
    path = run_dir / item['snapshot']
    if path.resolve().parent != run_dir.resolve():
        raise ValueError('Snapshot must belong to its run directory')
    body = path.read_bytes()
    if hashlib.sha256(body).hexdigest() != item.get('snapshot_sha256', source.sha256):
        raise ValueError('Raw snapshot hash mismatch')
    return json.loads(body), source


def fetch_source(url: str) -> tuple[bytes, Source]:
    with urlopen(Request(url, headers={'User-Agent': 'GameDiscoveryCatalog/0.2'}), timeout=20) as response:
        body = response.read(2 * 1024 * 1024 + 1)
        if response.status != 200 or len(body) > 2 * 1024 * 1024:
            raise ValueError('Invalid bounded source response')
    return body, Source(url=url, collected_at=datetime.now(UTC), sha256=hashlib.sha256(body).hexdigest())


def record_collection_failure(run_dir: Path, app_id: int, phase: str, observation: dict) -> None:
    failure = {'app_id': app_id, 'phase': phase, 'observed_at': datetime.now(UTC).isoformat(),
               **{key: observation[key] for key in ('error_type', 'review_error_type', 'http_status', 'retry_after')
                  if key in observation}}
    with (run_dir / 'collection-failures.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(failure) + '\n')


def collect(run_dir: Path, app_ids: list[int], resume: bool, reviews: bool = False,
            eligible_target: int | None = None) -> dict:
    if (not isinstance(app_ids, list) or not 1 <= len(app_ids) <= MAX_COLLECTION_IDS
            or any(type(value) is not int or not 0 < value <= 2147483647 for value in app_ids)
            or len(set(app_ids)) != len(app_ids)):
        raise ValueError('Collection requires 1–2500 distinct positive 32-bit IDs')
    if eligible_target is not None and (type(eligible_target) is not int or not 1 <= eligible_target <= min(2000, len(app_ids))):
        raise ValueError('Eligible target must be within 1–2000 and the candidate manifest')
    path = run_dir / "collection.json"
    report = {'schema_version': 2, 'region': 'US', 'app_ids': app_ids, 'reviews_requested': reviews,
              'eligible_target': eligible_target, 'observations': []}
    if path.exists():
        if not resume:
            raise ValueError("Existing run requires --resume")
        report = json.loads(path.read_text(encoding="utf-8"))
        if (report['app_ids'] != app_ids or report.get('reviews_requested', False) != reviews
                or report.get('eligible_target') != eligible_target):
            raise ValueError('Resume identity/settings mismatch')
    observed = {item['app_id']: item for item in report['observations']}
    eligible = 0
    report.pop('stopped', None)
    run_dir.mkdir(parents=True, exist_ok=True)
    for app_id in app_ids:
        if eligible_target is not None and eligible >= eligible_target:
            break
        previous = observed.get(app_id)
        observation = (previous or {'app_id': app_id}).copy()
        if observation.get('source') and not observation.get('error_type'):
            payload, source = source_payload(run_dir, observation)
        else:
            observation = {'app_id': app_id}
            try:
                url = f'https://store.steampowered.com/api/appdetails?appids={app_id}&cc=us&l=english'
                body, source = fetch_source(url)
                snapshot = run_dir / f'{app_id}-appdetails.json'
                snapshot.write_bytes(body)
                observation.update(snapshot=snapshot.name, source=source.model_dump(mode='json'))
                payload = json.loads(body)
                # Unavailable identities are per-ID failures, not access/throttle bypasses.
                game = normalize_payload(app_id, payload, source)
                observation.update(snapshot=snapshot.name, source=source.model_dump(mode='json'),
                                   eligibility=game.eligibility, eligibility_reason=game.eligibility_reason)
            except Exception as error:
                observation.update(error_type=type(error).__name__)
                unavailable = (isinstance(error, ValueError) and str(error) == 'Unverified app identity')
                if isinstance(error, HTTPError):
                    observation.update(http_status=error.code, retry_after=((error.headers or {}).get('Retry-After') or '')[:128])
                if not unavailable:
                    report['stopped'] = {'app_id': app_id, 'phase': 'appdetails', 'error_type': type(error).__name__}
                record_collection_failure(run_dir, app_id, 'appdetails', observation)
            finally:
                time.sleep(2)
        if not observation.get('error_type'):
            game = normalize_payload(app_id, payload, source)
            observation.update(eligibility=game.eligibility, eligibility_reason=game.eligibility_reason)
            if game.eligibility == 'eligible' and game.description:
                if reviews:
                    if observation.get('reviews'):
                        source_payload(run_dir, observation['reviews'])
                    else:
                        try:
                            params = {'appid': app_id, 'filter': 0, 'languages': ['all'], 'purchase_type': 1,
                                      'review_type': 0, 'num_per_page': 1, 'day_range': 0,
                                      'filter_offtopic_activity': True, 'display_language': 'english'}
                            url = 'https://api.steampowered.com/IUserReviewsService/GetAppReviews/v1/?' + urlencode({'input_json': json.dumps(params)})
                            body, review_source = fetch_source(url)
                            response = json.loads(body)
                            response = response.get('response', response)
                            summary = verified_review_summary({'success': 1, 'query_summary': response.get('query_summary')}, True)
                            if summary is None:
                                raise ValueError('Invalid review summary')
                            # Retain a hashed summary projection, not public authors/review text.
                            snapshot = run_dir / f'{app_id}-reviews.json'
                            write_json(snapshot, {'app_id': app_id, 'scope': REVIEW_SCOPE, 'summary': summary})
                            observation['reviews'] = {'snapshot': snapshot.name,
                                'snapshot_sha256': hashlib.sha256(snapshot.read_bytes()).hexdigest(),
                                'source': review_source.model_dump(mode='json'), 'projection': 'summary-only-v1'}
                            observation.pop('review_error_type', None)
                        except Exception as error:
                            observation['review_error_type'] = type(error).__name__
                            if isinstance(error, HTTPError):
                                observation.update(http_status=error.code, retry_after=((error.headers or {}).get('Retry-After') or '')[:128])
                            report['stopped'] = {'app_id': app_id, 'phase': 'reviews', 'error_type': type(error).__name__}
                            record_collection_failure(run_dir, app_id, 'reviews', observation)
                        finally:
                            time.sleep(2)
                if not observation.get('review_error_type'):
                    eligible += 1
        if observation == previous and not report.get('stopped'):
            continue
        observed[app_id] = observation
        report['observations'] = [observed[value] for value in app_ids if value in observed]
        report['eligible_complete'] = eligible
        write_json(path, report)
        print(json.dumps({'app_id': app_id, 'eligible_complete': eligible,
                          'observed': len(report['observations']), 'stopped': report.get('stopped')}), flush=True)
        if report.get('stopped'):
            break
    if report.get('eligible_complete') != eligible:
        report['eligible_complete'] = eligible
        write_json(path, report)
    return report


def normalize(run_dir: Path, metadata: bool = False, target_count: int | None = None,
              required_ids: list[int] | None = None) -> dict:
    report = json.loads((run_dir / "collection.json").read_text(encoding="utf-8"))
    if report.get('eligible_target') is not None and (
            report.get('stopped') or report.get('eligible_complete') != report['eligible_target']
            or target_count not in (None, report['eligible_target'])):
        raise ValueError('Collection must reach its configured eligible target before normalization')
    if report.get('reviews_requested') and not metadata:
        raise ValueError('Review-enabled collection requires metadata normalization')
    games = []
    quarantine = []
    dashboard = []
    for item in report["observations"]:
        if not item.get("source"):
            quarantine.append({"app_id": item["app_id"], "reason": "collection_failed"})
            continue
        if item.get('error_type'):
            quarantine.append({'app_id': item['app_id'], 'reason': 'collection_failed'})
            continue
        payload, source = source_payload(run_dir, item)
        game = normalize_payload(item['app_id'], payload, source)
        if game.eligibility != "eligible" or not game.description:
            quarantine.append({"app_id": game.app_id, "reason": game.eligibility_reason if game.description else "missing_description"})
            continue
        games.append(game.model_dump(mode="json"))
        if metadata:
            review_payload = review_source = None
            if item.get('reviews'):
                projection, review_source = source_payload(run_dir, item['reviews'])
                if projection.get('app_id') != game.app_id or projection.get('scope') != REVIEW_SCOPE:
                    raise ValueError('Review projection identity/scope mismatch')
                review_payload = projection['summary']
            dashboard.append(normalize_metadata(game.app_id, payload[str(game.app_id)]['data'], source,
                                                review_payload, review_source).model_dump(mode='json'))
        if target_count is not None and len(games) >= target_count:
            break
    games.sort(key=lambda game: game["app_id"])
    if not games:
        raise ValueError("No eligible games")
    if (target_count is not None and (not 1 <= target_count <= 2000 or len(games) != target_count)
            or set(required_ids or []) - {game['app_id'] for game in games}):
        write_json(run_dir / 'normalization-progress.json', {'eligible': len(games), 'target': target_count,
                   'quarantine': quarantine, 'missing_required_ids': sorted(set(required_ids or []) - {g['app_id'] for g in games})})
        raise ValueError('Eligible target or retained identities not met')
    write_json(run_dir / "games.json", games)
    result = {"schema_version": 1, "games": len(games), "requested": len(report["app_ids"]),
              "quarantine": quarantine, "games_sha256": digest(games), "model_id": MODEL_ID,
               "model_revision": MODEL_REVISION, "dimensions": 384, "semantic_text_version": "title-terms-description-v1"}
    if metadata:
        dashboard.sort(key=lambda item: item['app_id'])
        write_json(run_dir / 'metadata.json', dashboard)
        result.update(schema_version=2, metadata_format='dashboard-fields-v1', metadata_sha256=digest(dashboard))
    if target_count is not None:
        result['selection'] = {'eligible_target': target_count, 'required_ids': sorted(set(required_ids or [])),
                               'candidate_ids_sha256': digest(report['app_ids'])}
    write_json(run_dir / "normalized.json", result)
    return result


def load_metadata(run_dir: Path, manifest: dict, games: list[Game]) -> list[DashboardMetadata]:
    if manifest.get('schema_version') == 1:
        return []
    documents = json.loads((run_dir / 'metadata.json').read_text(encoding='utf-8'))
    if (manifest.get('metadata_format') != 'dashboard-fields-v1' or digest(documents) != manifest.get('metadata_sha256')
            or len(documents) != len(games)):
        raise ValueError('Dashboard metadata checksum/count mismatch')
    metadata = [DashboardMetadata.model_validate(item) for item in documents]
    if [item.app_id for item in metadata] != [game.app_id for game in games]:
        raise ValueError('Dashboard metadata identity mismatch')
    return metadata


def load_games(run_dir: Path) -> tuple[list[Game], dict]:
    manifest = json.loads((run_dir / "normalized.json").read_text(encoding="utf-8"))
    documents = json.loads((run_dir / "games.json").read_text(encoding="utf-8"))
    if digest(documents) != manifest["games_sha256"] or len(documents) != manifest["games"]:
        raise ValueError("Normalized artifact mismatch")
    games = [Game.model_validate(document) for document in documents]
    if len({game.app_id for game in games}) != len(games) or any(game.eligibility != "eligible" for game in games):
        raise ValueError("Invalid publication identities or eligibility")
    if manifest.get('schema_version') not in (1, 2):
        raise ValueError('Unsupported normalized format')
    load_metadata(run_dir, manifest, games)
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
    parts_dir = run_dir / 'embedding-parts'
    settings_path = run_dir / "embedding-settings.json"
    reusable = resume and (checkpoint.exists() or parts_dir.exists())
    if reusable and (not settings_path.exists() or json.loads(settings_path.read_text(encoding='utf-8')) != representation):
        raise ValueError('Checkpoint model representation mismatch')
    vectors = json.loads(checkpoint.read_text(encoding='utf-8')) if reusable and checkpoint.exists() else []
    write_json(settings_path, representation)
    expected = {game.app_id: game.semantic_hash for game in games}
    vectors = [Embedding.model_validate(item).model_dump() for item in vectors
               if expected.get(item["app_id"]) == item["semantic_hash"]]
    if len({item["app_id"] for item in vectors}) != len(vectors):
        raise ValueError("Duplicate embedding checkpoint")
    done = {item["app_id"] for item in vectors}
    if reusable:
        for game in games:
            part = parts_dir / f'{game.app_id}.json'
            if game.app_id in done or not part.exists():
                continue
            cached = Embedding.model_validate(json.loads(part.read_text(encoding='utf-8')))
            if cached.app_id != game.app_id:
                raise ValueError('Embedding part identity mismatch')
            if cached.semantic_hash == game.semantic_hash:
                vectors.append(cached.model_dump())
                done.add(game.app_id)
    pending = [game for game in games if game.app_id not in done]
    started = time.perf_counter()
    for offset in range(0, len(pending), batch_size):
        batch = pending[offset:offset + batch_size]
        encoded = encoder.encode([semantic_text(game) for game in batch])
        for game, vector in zip(batch, encoded, strict=True):
            item = Embedding(app_id=game.app_id, semantic_hash=game.semantic_hash, vector=vector.tolist()).model_dump()
            write_json(parts_dir / f'{game.app_id}.json', item)
            vectors.append(item)
    vectors.sort(key=lambda item: item['app_id'])
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


def database_manifest(artifact: dict) -> dict:
    """Keep unbounded rejection details locally, bound to the stored manifest by hash."""
    return {key: value for key, value in artifact.items() if key != 'quarantine'} | {
        'quarantine_count': len(artifact.get('quarantine', [])),
        'quarantine_sha256': digest(artifact.get('quarantine', [])),
        'artifact_sha256': digest(artifact),
    }


def publish(run_dir: Path, env_file: Path, activate: bool) -> dict:
    games, embeddings, artifact = validated_artifact(run_dir)
    dashboard_metadata = load_metadata(run_dir, artifact, games)
    analytics = analytics_manifest = None
    if artifact.get('schema_version') == 2:
        from game_discovery.catalog.analytics import build_analytics
        analytics = build_analytics(games, dashboard_metadata, artifact['version']).model_dump(mode='json')
        analytics_manifest = {'format': analytics['format'], 'catalog_version': artifact['version'],
                              'sha256': digest(analytics), 'artifact_sha256': digest(artifact),
                              'games_sha256': artifact['games_sha256'], 'metadata_sha256': artifact['metadata_sha256']}
        for filename, content in [('analytics.json', analytics), ('analytics-manifest.json', analytics_manifest)]:
            path = run_dir / filename
            if path.exists() and json.loads(path.read_text(encoding='utf-8')) != content:
                raise ValueError('Existing analytics artifact mismatch; use a new generation for changed aggregation')
            write_json(path, content)
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
                # The measured row-at-a-time pilot projects to ~26 minutes for 2,000.
                for offset in range(0, len(games), 100):
                    batch = games[offset:offset + 100]
                    connection.execute(text("""insert into discovery.games
                        (version,app_id,title,normalized_title,description,eligibility,semantic_hash,document,identity_title,compact_title,title_tokens)
                        values (:v,:id,:title,:normalized,:description,:eligibility,:hash,cast(:doc as jsonb),:identity,:compact,:tokens)"""),
                        [{'v': version, 'id': game.app_id, "title": game.title, "normalized": game.title.casefold(), "description": game.description,
                           'eligibility': game.eligibility, 'hash': game.semantic_hash, 'doc': game.model_dump_json(),
                           'identity': normalize_title(game.title), 'compact': normalize_title(game.title).replace(' ', ''),
                           'tokens': normalize_title(game.title).split()} for game in batch])
                    connection.execute(text("insert into discovery.game_platforms values (:v,:id,:platform,:supported)"),
                                       [{'v': version, 'id': game.app_id, 'platform': platform, 'supported': supported}
                                        for game in batch for platform, supported in game.platforms.items()])
                    terms = [{'v': version, 'id': game.app_id, 'kind': kind, 'term': term}
                             for game in batch for kind, values in (('genre', game.genres), ('tag', game.tags), ('mode', game.modes))
                             for term in sorted(set(values))]
                    if terms:
                        connection.execute(text("insert into discovery.game_terms values (:v,:id,:kind,:term)"), terms)
                    connection.execute(text("insert into discovery.game_prices values (:v,:id,:amount,:free,'US','USD',:observed)"),
                                       [{'v': version, 'id': game.app_id, "amount": game.price.amount_cents if game.price else None,
                                         "free": game.free_to_play, "observed": game.price.observed_at if game.price else None} for game in batch])
                    connection.execute(text("insert into discovery.game_embeddings values (:v,:id,:hash,cast(:vector as extensions.vector))"),
                                        [{'v': version, 'id': game.app_id, "hash": game.semantic_hash,
                                          "vector": json.dumps(vectors[game.app_id].vector)} for game in batch])
                for offset in range(0, len(dashboard_metadata), 100):
                    connection.execute(text('insert into discovery.game_dashboard_metadata values(:v,:id,cast(:doc as jsonb))'),
                                       [{'v': version, 'id': item.app_id, 'doc': item.model_dump_json()}
                                        for item in dashboard_metadata[offset:offset + 100]])
                connection.execute(text('update discovery.catalog_versions set artifact_manifest=cast(:manifest as jsonb) where version=:v'),
                                   {'v': version, 'manifest': json.dumps(database_manifest(artifact))})
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
            stored_keys = list(connection.execute(text('select app_id,identity_title,compact_title,title_tokens from discovery.games where version=:v order by app_id'), {'v': version}))
            if [tuple(row) for row in stored_keys] != [(g.app_id, normalize_title(g.title), normalize_title(g.title).replace(' ', ''), normalize_title(g.title).split()) for g in games]:
                raise ValueError('Staged title identities mismatch')
            if artifact.get('schema_version') == 2:
                expected_metadata = load_metadata(run_dir, artifact, games)
                stored_metadata = [row[0] for row in connection.execute(text('select document from discovery.game_dashboard_metadata where version=:v order by app_id'), {'v': version})]
                stored_manifest = connection.execute(text('select artifact_manifest from discovery.catalog_versions where version=:v'), {'v': version}).scalar_one()
                if stored_metadata != [item.model_dump(mode='json') for item in expected_metadata] or stored_manifest != database_manifest(artifact):
                    raise ValueError('Staged metadata/manifest mismatch')
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
            if analytics is not None and analytics_manifest is not None:
                stored_analytics = connection.execute(text('select sha256,document from discovery.catalog_analytics where version=:v'), {'v': version}).one_or_none()
                stored_binding = connection.execute(text('select analytics_manifest from discovery.catalog_versions where version=:v'), {'v': version}).scalar_one()
                if stored_analytics is None and stored_binding is None:
                    connection.execute(text('insert into discovery.catalog_analytics(version,sha256,document) values(:v,:sha,cast(:doc as jsonb))'),
                                       {'v': version, 'sha': analytics_manifest['sha256'], 'doc': json.dumps(analytics)})
                    connection.execute(text('update discovery.catalog_versions set analytics_manifest=cast(:manifest as jsonb) where version=:v'),
                                       {'v': version, 'manifest': json.dumps(analytics_manifest)})
                elif (stored_analytics is None or tuple(stored_analytics) != (analytics_manifest['sha256'], analytics)
                      or stored_binding != analytics_manifest):
                    raise ValueError('Staged analytics/manifest mismatch')
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
        if analytics_manifest:
            result['analytics_sha256'] = analytics_manifest['sha256']
        if activate:
            result["previous_version"] = previous
        write_json(run_dir / ("activation-report.json" if activate else "import-report.json"), result)
        return result
    finally:
        engine.dispose()
