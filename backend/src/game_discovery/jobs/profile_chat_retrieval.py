"""Read-only development-query latency/SQL profile; no inference or reservations."""

import argparse
import json
import time
from pathlib import Path

from sqlalchemy import event, text

from game_discovery.catalog.contracts import Filters
from game_discovery.catalog.repository import CatalogRepository
from game_discovery.core.settings import Settings
from game_discovery.db.engine import create_runtime_engine
from game_discovery.jobs.chat_evaluation import percentile
from game_discovery.jobs.evaluate_chat import save
from game_discovery.retrieval.chat import ChatRetriever
from game_discovery.retrieval.query import load_query_encoder


def run(output: Path, samples: int) -> None:
    if output.exists() or not output.parent.is_dir():
        raise ValueError("new_output_in_existing_parent_required")
    settings = Settings.from_environment()
    encoder = load_query_encoder(settings.query_tokenizer_path, settings.query_model_path, settings.query_artifact_path)
    engine = create_runtime_engine(settings.database_url)
    if encoder is None or engine is None:
        raise ValueError("configured_encoder_and_database_required")
    statements, rows, explain = [], [], None
    def before(connection, cursor, statement, parameters, context, executemany):
        context.profile_started = time.perf_counter()
    def after(connection, cursor, statement, parameters, context, executemany):
        nonlocal explain
        statements.append({"operation": statement.strip().split()[0],
                           "duration_ms": (time.perf_counter() - context.profile_started) * 1000})
        if "lexical_pool" in statement:
            explain = (statement, parameters)
    event.listen(engine, "before_cursor_execute", before)
    event.listen(engine, "after_cursor_execute", after)
    repository = CatalogRepository(engine)
    retriever = ChatRetriever(repository, encoder)
    try:
        for index in range(samples + 1):
            for kind, query in (("recommend", "multiplayer games"), ("title", "spiderman"),
                                ("recommend", "tending a farm and getting to know a small town")):
                start = len(statements)
                clock = time.perf_counter()
                result = (retriever.lookup_title(query) if kind == "title" else
                          retriever.recommend(query, Filters()))
                rows.append({"warm": index > 0, "kind": kind, "query": query,
                             "duration_ms": (time.perf_counter() - clock) * 1000,
                             "ids": [c.game.app_id for c in result.candidates],
                             "outcome": result.outcome.model_dump(), "sql": statements[start:]})
        plan = None
        if explain:
            statement, parameters = explain
            with repository.snapshot() as (connection, _):
                guards = dict(connection.execute(text("""select current_setting('transaction_read_only') as read_only,
                    current_setting('transaction_isolation') as isolation,
                    current_setting('statement_timeout') as timeout""")).mappings().one())
                plan = connection.exec_driver_sql("EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + statement,
                                                 parameters).scalar_one()
            with engine.connect() as connection:
                reset = dict(connection.execute(text("""select current_setting('transaction_read_only') as read_only,
                    current_setting('statement_timeout') as timeout""")).mappings().one())
        report = {"scope": "fixed development queries only; no provider/reservation; cold first cycle excluded",
                  "samples": rows, "explain": plan, "transaction_guards": guards, "pool_reset": reset,
                  "warm_p95_ms": percentile([r["duration_ms"] for r in rows if r["warm"]]),
                  "warm_p95_by_kind": {kind: percentile([r["duration_ms"] for r in rows
                      if r["warm"] and r["kind"] == kind]) for kind in ("title", "recommend")}}
        save(output, report)
        print(json.dumps({k: report[k] for k in ("warm_p95_ms", "warm_p95_by_kind")}))
    finally:
        engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, choices=range(1, 31), default=4)
    args = parser.parse_args()
    run(args.output, args.samples)


if __name__ == "__main__":
    main()
