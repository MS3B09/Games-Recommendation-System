"""Prepare null owner judgments or score actual supplied retrieval judgments.

Missing judgments block aggregate comparison; no builder-generated relevance.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path


def template(report: dict) -> dict:
    return {'source_report_sha256': hashlib.sha256(json.dumps(report, sort_keys=True).encode()).hexdigest(),
        'rubric': 'Owner only: 0 irrelevant, 1 plausible, 2 strong fit. Empty-ranking adequacy: pass/partial/fail.',
        'cases': {row['id']: {'relevance': {str(app_id): None for app_id in sorted({i for ids in row['rankings'].values() for i in ids})},
            'empty_ranking_adequacy': {label: None for label, method in row['masked_methods'].items() if not row['rankings'][method]},
            'notes': None} for row in report['results']}}


def score(report: dict, judgments: dict) -> dict:
    expected = template(report)
    if (judgments.get('source_report_sha256') != expected['source_report_sha256']
            or set(judgments.get('cases', {})) != set(expected['cases'])):
        raise ValueError('Wrong source report or case identities')
    rows = []
    for row in report['results']:
        supplied = judgments['cases'][row['id']]
        target = expected['cases'][row['id']]
        if (set(supplied.get('relevance', {})) != set(target['relevance'])
                or set(supplied.get('empty_ranking_adequacy', {})) != set(target['empty_ranking_adequacy'])):
            raise ValueError('Missing or unknown candidate/masked ranking identities')
        ratings = supplied['relevance']
        if any(value is not None and (type(value) is not int or value not in (0, 1, 2)) for value in ratings.values()):
            raise ValueError('Owner relevance must be null or integer 0, 1, 2')
        adequacy = supplied['empty_ranking_adequacy']
        if any(value not in (None, 'pass', 'partial', 'fail') for value in adequacy.values()):
            raise ValueError('Invalid empty-ranking adequacy judgment')
        missing = sum(value is None for value in [*ratings.values(), *adequacy.values()])
        methods = None
        if not missing:
            ideal = sorted(ratings.values(), reverse=True)[:4]
            ideal_dcg = sum((2**rating - 1) / math.log2(index + 2) for index, rating in enumerate(ideal))
            methods = {}
            for method, ids in row['rankings'].items():
                gains = [ratings[str(app_id)] for app_id in ids]
                dcg = sum((2**rating - 1) / math.log2(index + 2) for index, rating in enumerate(gains))
                methods[method] = {'mean_gain_at_4': sum(gains) / 4,
                    'precision_at_4': sum(value >= 1 for value in gains) / 4,
                    'ndcg_at_4_judged_union': dcg / ideal_dcg if ideal_dcg else 0.0}
        rows.append({'id': row['id'], 'split': row['split'], 'missing_judgments': missing, 'metrics': methods,
                     'empty_ranking_adequacy': adequacy})
    summaries = {}
    for split in ('development', 'held_out'):
        selected = [row for row in rows if row['split'] == split]
        missing = sum(row['missing_judgments'] for row in selected)
        aggregate = None
        if selected and not missing:
            aggregate = {method: {metric: sum(row['metrics'][method][metric] for row in selected) / len(selected)
                for metric in ('mean_gain_at_4', 'precision_at_4', 'ndcg_at_4_judged_union')}
                for method in ('hybrid_rrf', 'cosine_only')}
            aggregate['paired_mean_gain_difference'] = aggregate['hybrid_rrf']['mean_gain_at_4'] - aggregate['cosine_only']['mean_gain_at_4']
        summaries[split] = {'cases': len(selected), 'missing_judgments': missing, 'aggregate': aggregate}
    return {'status': 'owner_judgments_incomplete' if any(row['missing_judgments'] for row in rows) else 'owner_judgments_scored',
        'splits': summaries, 'cases': rows,
        'scope': 'Retrieval-only owner judgments. No whole-catalog recall, generated-answer quality, or final acceptance claim.'}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', required=True, type=Path)
    parser.add_argument('--judgments', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if not args.output.parent.is_dir() or args.output.exists():
        parser.error('Use a fresh output file with an existing parent; never overwrite owner ratings.')
    report = json.loads(args.report.read_text(encoding='utf-8'))
    result = score(report, json.loads(args.judgments.read_text(encoding='utf-8'))) if args.judgments else template(report)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'status': result.get('status', 'prepared_null_owner_judgments'), 'inference_calls': 0}))


if __name__ == '__main__':
    main()
