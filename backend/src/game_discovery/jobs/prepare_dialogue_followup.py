"""Freeze an empty live-evaluation checkpoint without HTTP, SQL or inference."""
import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from game_discovery.core.settings import Settings
from game_discovery.jobs.evaluate_dialogue_live import identity, save


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases', required=True, type=Path)
    parser.add_argument('--split', choices=['development', 'held_out'], required=True)
    parser.add_argument('--case-order', required=True, nargs='+')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[4]
    authority = Path('C:/Users/User/AppData/Local/Temp/opencode').resolve()
    if args.output.parent.resolve() != authority or not authority.is_dir() or '.private.' in args.output.name:
        parser.error('Use an ordinary public journal in the approved authoritative C: directory.')
    cases_path = args.cases.resolve()
    cases = json.loads(cases_path.read_text(encoding='utf-8'))[args.split]
    if len(args.case_order) != len(cases) or set(args.case_order) != {case['id'] for case in cases}:
        parser.error('Case order must contain every selected case exactly once.')
    settings = Settings.from_environment()
    configuration = {'model': settings.groq_model, 'daily_calls': settings.ai_daily_calls,
        'daily_reserved_units': settings.ai_daily_tokens, 'max_model_calls_per_turn': 3,
        'max_tool_calls_per_turn': 6, 'provider_input_bytes': 12000, 'case_order': args.case_order}
    current = identity(root, cases_path)
    if args.output.exists():
        existing = json.loads(args.output.read_text(encoding='utf-8'))
        if (existing.get('source_identity') != current or existing.get('runtime_configuration') != configuration
                or existing.get('split') != args.split):
            parser.error('Existing checkpoint differs; preserve it and use a new version. No overwrite performed.')
        print(json.dumps({'status': 'existing_checkpoint_unchanged', 'inference_calls': 0}))
        return
    save(args.output, {'version': 'llm-first-v1', 'split': args.split, 'source_identity': current,
        'runtime_configuration': configuration, 'cases': [], 'human_scores': None,
        'prepared_without_inference_at': datetime.now(UTC).isoformat()})
    print(json.dumps({'status': 'prepared_without_inference', 'inference_calls': 0,
        'case_order': args.case_order, 'planned_turns': sum(len(case['turns']) for case in cases)}))


if __name__ == '__main__':
    main()
