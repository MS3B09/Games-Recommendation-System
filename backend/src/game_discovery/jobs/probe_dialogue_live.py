"""Single-attempt development smoke via the real HTTP/quota boundary.

Stores a public result without chat capabilities. No automatic retry or R4 replay.
"""
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4


def post(path: str, value: dict) -> tuple[int, dict]:
    req = Request('http://127.0.0.1:8001' + path, json.dumps(value).encode(), {'Content-Type': 'application/json'})
    try:
        with urlopen(req, timeout=75) as response:
            return response.status, json.load(response)
    except HTTPError as error:
        return error.code, json.load(error)


def main() -> None:
    root = Path(__file__).resolve().parents[4]
    output = root / 'docs/reports/llm-first-development-smoke.json'
    if output.exists():
        raise SystemExit('Single-attempt smoke already recorded; preserve its evidence.')
    status, created = post('/api/v2/assistant/conversations', {'messages': []})
    if status != 200:
        print(json.dumps({'stage': 'create', 'status': status, 'response': created}))
        return
    key = {k: created[k] for k in ('conversation_id', 'token')}
    record = {'at': datetime.now(UTC).isoformat(), 'status': 'started', 'message': 'Hi! I had a long day and just want to chat for a moment.'}
    output.write_text(json.dumps(record, indent=2), encoding='utf-8')
    try:
        status, response = post('/api/v2/assistant', {**key, 'revision': 0, 'turn_id': str(uuid4()), 'message': record['message']})
        record.update(status=status, response=response)
        _, history = post('/api/v2/assistant/history', key)
        record['archive'] = history
    finally:
        record['cleanup_status'] = post('/api/v2/assistant/forget', key)[0]
        output.write_text(json.dumps(record, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'status': status, 'response': response}, ensure_ascii=True))


if __name__ == '__main__':
    main()
