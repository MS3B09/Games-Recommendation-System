"""Read-only paired native retrieval evaluation; no model or quota operations.

The same encoder, query, oracle filters and candidate SQL feed RRF and cosine.
Owner relevance judgments remain empty; mechanical checks are not quality scores.
"""
import argparse
import hashlib
import json
import math
import random
import time
from datetime import UTC, datetime
from pathlib import Path


def p95(values: list[float]) -> float:
    return sorted(values)[max(0, math.ceil(len(values) * .95) - 1)]


def run(cases_path: Path) -> dict:
    from game_discovery.catalog.contracts import Filters
    from game_discovery.catalog.discovery import satisfies
    from game_discovery.catalog.repository import CatalogRepository
    from game_discovery.core.settings import Settings
    from game_discovery.db.engine import create_runtime_engine
    from game_discovery.jobs.encoder_parity import MemorySampler
    from game_discovery.jobs.evaluate_dialogue_live import identity
    from game_discovery.retrieval.chat import ChatRetriever
    from game_discovery.retrieval.query import load_query_encoder

    root = Path(__file__).resolve().parents[4]
    fixture = json.loads(cases_path.read_text(encoding='utf-8'))
    settings = Settings.from_environment()
    engine = create_runtime_engine(settings.database_url)
    repo = CatalogRepository(engine)
    results = []
    catalog_versions = set()
    randomizer = random.Random(20261030)
    try:
        with MemorySampler() as memory:
            started = time.perf_counter()
            encoder = load_query_encoder(settings.query_tokenizer_path, settings.query_model_path, settings.query_artifact_path)
            if encoder is None:
                raise RuntimeError('The actual configured pinned encoder is required; no lexical substitute.')
            encoder_load_ms = (time.perf_counter() - started) * 1000

            class ObservedRepository:
                pools = None

                def chat_title(self, query, reference_id=None):
                    return repo.chat_title(query, reference_id)

                def chat_candidates(self, *args, **kwargs):
                    self.pools = repo.chat_candidates(*args, **kwargs)
                    return self.pools

            observed = ObservedRepository()
            retriever = ChatRetriever(observed, encoder)
            for split in ('development', 'held_out'):
                for case in fixture[split]:
                    filters = Filters.model_validate(case['filters'])
                    started = time.perf_counter()
                    ranked = retriever.recommend(case['query'], filters)
                    elapsed = (time.perf_counter() - started) * 1000
                    if observed.pools is None or not ranked.outcome.semantic_available:
                        raise RuntimeError('Semantic retrieval unavailable; preserve failure rather than score fallback.')
                    catalog_versions.add(ranked.catalog_version)
                    proposed = [candidate.game for candidate in ranked.candidates[:4]]
                    baseline = [game for game, score in observed.pools.semantic[:4]]
                    methods = {'hybrid_rrf': proposed, 'cosine_only': baseline}
                    violations = {method: [game.app_id for game in games if not satisfies(game, filters, set(filters.excluded_ids))]
                                  for method, games in methods.items()}
                    labels = ['hybrid_rrf', 'cosine_only']
                    randomizer.shuffle(labels)
                    results.append({'id': case['id'], 'split': split, 'request': case['turns'][0],
                        'query': case['query'], 'oracle_filters': filters.model_dump(exclude_defaults=True),
                        'catalog_version': ranked.catalog_version, 'shared_retrieve_encode_ms': round(elapsed, 3),
                        'outcome': ranked.outcome.model_dump(), 'hard_violations': violations,
                        'masked_methods': {label: method for label, method in zip(('A', 'B'), labels, strict=True)},
                        'rankings': {method: [game.app_id for game in games] for method, games in methods.items()},
                        'candidates': {str(game.app_id): game.model_dump(mode='json') for games in methods.values() for game in games},
                        'owner_relevance': None, 'owner_notes': None})
            # Full explicit catalog traversal proves an eligibility delta, unlike
            # a repeated top-ranked card. This is not a generated conversation.
            catalog = []
            offset = 0
            while True:
                page = repo.assistant_search('', 30, offset)
                catalog_versions.add(page.catalog_version)
                catalog.extend(page.items)
                offset += len(page.items)
                if offset >= page.total:
                    break
                if not page.items:
                    raise RuntimeError('Incomplete catalog traversal')
            normal = Filters(platforms=['windows'], required_modes=['single-player'], max_price_cents=1000)
            temporary = normal.model_copy(update={'max_price_cents': 2000})
            normal_ids = {g.app_id for g in catalog if satisfies(g, normal, set())}
            temporary_ids = {g.app_id for g in catalog if satisfies(g, temporary, set())}
            expanded = [g for g in catalog if g.app_id in temporary_ids - normal_ids]
            if not expanded or any(any(record['hard_violations'].values()) for record in results):
                raise AssertionError('Temporary eligibility or hard-constraint check failed')
            if len(catalog_versions) != 1 or encoder.catalog_version not in catalog_versions:
                raise RuntimeError('Catalog version changed or encoder mismatch; do not combine observations')
            return {'version': 'native-assistant-retrieval-v1', 'measured_at': datetime.now(UTC).isoformat(),
                'status': 'mechanical_checks_passed_owner_relevance_pending',
                'fixture_sha256': hashlib.sha256(cases_path.read_bytes()).hexdigest(),
                'source_identity': identity(root, cases_path),
                'evaluator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'catalog_version': next(iter(catalog_versions)), 'catalog_records': len(catalog),
                'encoder_load_ms': round(encoder_load_ms, 3), 'peak_rss_mib': round(memory.peak / 1024**2, 3),
                'timing': {'samples': len(results), 'cold_first_query_ms': results[0]['shared_retrieve_encode_ms'],
                    'all_query_p95_ms': p95([r['shared_retrieve_encode_ms'] for r in results]),
                    'warm_query_p95_ms': p95([r['shared_retrieve_encode_ms'] for r in results[1:]])},
                'temporary_eligibility': {'normal_filters': normal.model_dump(exclude_defaults=True),
                    'temporary_filters': temporary.model_dump(exclude_defaults=True),
                    'normal_eligible_ids': sorted(normal_ids), 'temporary_eligible_ids': sorted(temporary_ids),
                    'newly_eligible': [{'id': g.app_id, 'title': g.title, 'recorded_cents': g.price.amount_cents} for g in expanded]},
                'results': results, 'live_model_calls': 0, 'actual_reservations': 0, 'database_writes': 0,
                'limitations': ['Oracle filters do not test model interpretation or final explanation quality.',
                    'Shared retrieval latency is not an independent per-method end-to-end speed comparison.',
                    'Human relevance and all improvement claims remain pending.',
                    'All builder-visible results are exposed for future tuning; do not relabel reused cases unseen.']}
    finally:
        engine.dispose()


def worksheet(report: dict) -> str:
    lines = ['# Native retrieval — masked owner review', '',
        'Rate each returned game **0 = irrelevant, 1 = plausible, 2 = strong fit** for the request. Leave missing judgments null; an empty ranking is no result, not a quality pass. Review in batches of five. A/B order varies by case. Do not infer a winner from mechanical checks.', '',
        'This compares rankings with the same catalog, encoder and oracle filters. It does not score generated assistant conversation. Raw method keys are in the separate result JSON; review this worksheet first.', '']
    for row in report['results']:
        lines += [f"## {row['id']} ({row['split']})", '', row['request'], '']
        for label, method in row['masked_methods'].items():
            lines += [f'### Ranking {label}', '']
            for app_id in row['rankings'][method]:
                game = row['candidates'][str(app_id)]
                lines += [f"- **{game['title']}** — {game['description'][:500]}", '  - Owner relevance: —; notes: —.']
            if not row['rankings'][method]:
                lines += ['- No matching results. Owner adequacy: —.']
            lines += ['']
    return '\n'.join(lines) + '\n'


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--worksheet', required=True, type=Path)
    args = parser.parse_args()
    if any(not path.parent.is_dir() or path.exists() for path in (args.output, args.worksheet)):
        parser.error('Existing parents and fresh output names required; preserve prior results.')
    report = run(args.cases.resolve())
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    args.worksheet.write_text(worksheet(report), encoding='utf-8')
    print(json.dumps({key: report[key] for key in ('status', 'catalog_records', 'timing', 'peak_rss_mib', 'live_model_calls')}))


if __name__ == '__main__':
    main()
