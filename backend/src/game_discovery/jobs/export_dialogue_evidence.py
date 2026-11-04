"""Export public synthetic journals from authoritative C: storage. No inference.

Never exports private capabilities, overwrites a differing snapshot, or restores
an older E: export over an authoritative C: journal.
"""
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[4]
    source_dir = Path('C:/Users/User/AppData/Local/Temp/opencode')
    target_dir = root / 'docs/reports'
    assert source_dir.is_dir() and target_dir.is_dir()
    names = ['llm-first-development-v6', 'llm-first-development-v7', 'llm-first-development-v8',
             'llm-first-development-v9', 'llm-first-held-out-v7', 'llm-first-held-out-v10',
             'llm-first-regression-v11', 'llm-first-regression-v12', 'llm-first-held-out-v13',
             'llm-first-development-v14', 'llm-first-held-out-v14',
             'llm-first-development-v15', 'llm-first-held-out-v15',
             'llm-first-development-v16', 'llm-first-held-out-v16',
             'llm-first-development-v17', 'llm-first-held-out-v17',
             'llm-first-development-v18', 'llm-first-held-out-v18',
             'llm-first-development-v19', 'llm-first-held-out-v19',
             'llm-first-development-v20', 'llm-first-held-out-v20', 'llm-first-held-out-v21']
    manifest = {'exported_at': datetime.now(UTC).isoformat(), 'authority': str(source_dir), 'snapshots': []}

    def public_only(value):
        if isinstance(value, dict):
            assert not {'token', 'secret', 'secret_hash', 'groq_api_key', 'database_url'}.intersection(value)
            for child in value.values():
                public_only(child)
        elif isinstance(value, list):
            for child in value:
                public_only(child)

    for name in names:
        source = source_dir / (name + '.json')
        if not source.is_file():
            continue
        raw = source.read_bytes()
        data = json.loads(raw)
        public_only(data)
        current_matches = None
        case_files = {'llm-first-held-out-v13': 'dialogue-v3.json',
                      'llm-first-development-v14': 'dialogue-v4.json', 'llm-first-held-out-v14': 'dialogue-v4.json',
                      'llm-first-development-v15': 'dialogue-v5.json', 'llm-first-held-out-v15': 'dialogue-v5.json',
                      'llm-first-development-v16': 'dialogue-v6.json', 'llm-first-held-out-v16': 'dialogue-v6.json',
                      'llm-first-development-v17': 'dialogue-v7.json', 'llm-first-held-out-v17': 'dialogue-v7.json',
                      'llm-first-development-v18': 'dialogue-v8.json', 'llm-first-held-out-v18': 'dialogue-v8.json',
                      'llm-first-development-v19': 'dialogue-v9.json', 'llm-first-held-out-v19': 'dialogue-v9.json',
                      'llm-first-development-v20': 'dialogue-v10.json', 'llm-first-held-out-v20': 'dialogue-v10.json',
                      'llm-first-held-out-v21': 'dialogue-v11.json'}
        if name in case_files:
            from game_discovery.jobs.evaluate_dialogue_live import identity
            current_matches = identity(root, root / 'data/evaluation' / case_files[name]) == data['source_identity']
        filename = name + ('-complete' if name == 'llm-first-development-v6' else '') + '.json'
        target = target_dir / filename
        if target.exists() and target.read_bytes() != raw:
            target = target_dir / (Path(filename).stem + '-snapshot-' + datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ') + '.json')
        if not target.exists():
            target.write_bytes(raw)
        assert target.read_bytes() == raw
        turns = [turn for case in data.get('cases', []) for turn in case.get('turns', [])]
        manifest['snapshots'].append({'source': str(source), 'export': target.name,
            'sha256': hashlib.sha256(raw).hexdigest(), 'attempted_turns': len(turns),
            'http_200_deliveries': sum(turn.get('status') == 200 for turn in turns),
            'paused': data.get('paused'), 'human_scores': data.get('human_scores'), 'current_source_matches': current_matches})
    (target_dir / 'llm-first-evidence-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(manifest, ensure_ascii=True))


if __name__ == '__main__':
    main()
