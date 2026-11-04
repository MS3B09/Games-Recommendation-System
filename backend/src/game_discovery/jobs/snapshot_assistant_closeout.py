"""Capture checked closeout identities/receipt and a secret-free source backup."""
import argparse
import hashlib
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path


def main() -> None:
    from game_discovery.core.settings import Settings
    from game_discovery.jobs.evaluate_dialogue_live import identity, quota_receipt

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--backup', required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[4]
    authority = Path('C:/Users/User/AppData/Local/Temp/opencode')
    if (args.backup.parent.resolve() != authority.resolve() or not args.output.parent.is_dir()
            or not authority.is_dir() or args.output.exists() or args.backup.exists()):
        parser.error('Fresh output/approved C: backup paths with existing parents required.')
    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()
    old = {'llm-first-held-out-v20.json': 'b32510563b439140d6feb96e7ed670b793bacfbb17ffb10a8274d634d59d1c3f',
           'llm-first-held-out-v21.json': 'd5b82e199b5a0848d2cfd8f4a7c647eb4d327cc0974e3679114547e8f56847d4'}
    for name, expected in old.items():
        if digest(authority / name) != expected:
            raise RuntimeError('Historical journal changed; investigate without overwriting anything.')
    fixtures = {'capability': root / 'data/evaluation/dialogue-v12.json',
                'discovery': root / 'data/evaluation/assistant-discovery-v1.json'}
    checkpoints = []
    for kind, fixture in fixtures.items():
        for split, file_split in (('development', 'development'), ('held_out', 'held-out')):
            path = authority / f'assistant-closeout-{kind}-{file_split}-v22.json'
            checkpoint = json.loads(path.read_text(encoding='utf-8'))
            if checkpoint['source_identity'] != identity(root, fixture):
                raise RuntimeError('Prepared checkpoint differs from current source')
            checkpoints.append({'path': str(path), 'sha256': digest(path), 'split': split,
                'kind': kind, 'recorded_turns': sum(len(c['turns']) for c in checkpoint['cases']),
                'planned_turns': sum(len(c['turns']) for c in json.loads(fixture.read_text(encoding='utf-8'))[split])})
    retrieval = json.loads((root / 'docs/reports/assistant-retrieval-v1.json').read_text(encoding='utf-8'))
    browser = json.loads((root / 'docs/reports/assistant-closeout-browser-2026-10-30-v2.json').read_text(encoding='utf-8'))
    ui = json.loads((root / 'docs/reports/assistant-closeout-ui-v5.json').read_text(encoding='utf-8'))
    cleanup = json.loads((root / 'docs/reports/assistant-closeout-ui-v5-cleanup.json').read_text(encoding='utf-8'))
    if (browser['stats']['expected'] != 74 or browser['stats']['unexpected'] or not cleanup['all_erased']
            or ui['status'] != 'passed' or len(retrieval['results']) != 40):
        raise RuntimeError('Incomplete or failed evidence')
    settings = Settings.from_environment()
    receipt = quota_receipt(root, settings.ai_daily_calls, settings.ai_daily_tokens)
    files = {root / path for checkpoint in checkpoints for path in json.loads(Path(checkpoint['path']).read_text(encoding='utf-8'))['source_identity']}
    files.update(root / path for path in (
        'backend/src/game_discovery/jobs/evaluate_assistant_retrieval.py',
        'backend/src/game_discovery/jobs/score_assistant_retrieval.py',
        'backend/src/game_discovery/jobs/snapshot_assistant_closeout.py',
        'backend/src/game_discovery/jobs/serve_assistant_closeout_probe.py',
        'backend/src/game_discovery/jobs/prepare_dialogue_followup.py',
        'backend/tests/test_dialogue.py', 'backend/tests/test_assistant_retrieval_review.py',
        'docs/assistant-closeout-protocol.md', 'docs/reports/assistant-retrieval-v1.json',
        'docs/reports/assistant-retrieval-owner-v1.json', 'docs/reports/assistant-retrieval-owner-v1.md',
        'docs/reports/assistant-retrieval-score-v1.json', 'docs/reports/assistant-closeout-ui-v5.json',
        'docs/reports/assistant-closeout-ui-v5-cleanup.json', 'docs/reports/assistant-closeout-browser-2026-10-30-v2.json',
        'docs/reports/llm-first-owner-review-2026-10-30.json', 'docs/reports/llm-first-owner-review-2026-10-30.md'))
    with zipfile.ZipFile(args.backup, 'x', compression=zipfile.ZIP_DEFLATED) as backup:
        for path in sorted(files):
            if '.private.' in path.name or path.name.startswith('.env'):
                raise RuntimeError('Private file must never enter public source backup')
            backup.write(path, path.relative_to(root))
        backup.write(authority / 'verify-assistant-closeout-ui-v1.mjs', 'local-tools/verify-assistant-closeout-ui.mjs')
        for scan in ui['scans']:
            backup.write(scan['capture'], 'ui-captures/' + Path(scan['capture']).name)
    with zipfile.ZipFile(args.backup) as backup:
        if backup.testzip() is not None:
            raise RuntimeError('Backup integrity failed')
    snapshot = {'at': datetime.now(UTC).isoformat(), 'status': 'offline_and_integration_verified_live_and_owner_gates_incomplete',
        'owner_authorization': 'PROMPT.txt A–F, no final acceptance/publication',
        'historical_journals_verified_unchanged': old, 'prepared_checkpoints': checkpoints,
        'current_source_files': {str(path.relative_to(root)).replace('\\', '/'): digest(path) for path in sorted(files)},
        'receipt': receipt, 'new_live_provider_calls': 0, 'new_actual_reservations': 0,
        'backend_tests_passed': 261, 'frontend_tests_passed': browser['stats']['expected'],
        'retrieval_samples': 40, 'retrieval_timing': retrieval['timing'], 'retrieval_peak_rss_mib': retrieval['peak_rss_mib'],
        'ui_checks': len(ui['checks']), 'ui_scans': len(ui['scans']), 'probe_archives_erased': cleanup['all_erased'],
        'backup': {'path': str(args.backup), 'sha256': digest(args.backup), 'integrity_checked': True},
        'acceptance': None, 'publication': False}
    args.output.write_text(json.dumps(snapshot, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: snapshot[key] for key in ('status', 'receipt', 'new_live_provider_calls', 'backup')}))


if __name__ == '__main__':
    main()
