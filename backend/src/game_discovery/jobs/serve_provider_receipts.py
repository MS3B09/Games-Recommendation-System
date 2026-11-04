"""Local observation-only launcher for provider rate-limit response headers.

Does not change serving modules, requests, responses, limits or retries. Never
records request headers/bodies, response bodies, URLs or conversation capabilities.
"""
import argparse
import hashlib
import json
import sys
import threading
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError
from unittest.mock import patch


RATE_HEADERS = (
    'retry-after',
    'x-ratelimit-limit-requests', 'x-ratelimit-remaining-requests', 'x-ratelimit-reset-requests',
    'x-ratelimit-limit-tokens', 'x-ratelimit-remaining-tokens', 'x-ratelimit-reset-tokens',
)


@contextmanager
def observe_headers(output: Path):
    from game_discovery.ai import provider

    original = provider.urlopen
    lock = threading.Lock()

    def record(status, headers):
        receipt = {'at': datetime.now(UTC).isoformat(), 'status': status,
                   'headers': {name: str(headers.get(name))[:128] for name in RATE_HEADERS
                               if headers is not None and headers.get(name) is not None}}
        try:
            with lock, output.open('a', encoding='utf-8') as target:
                target.write(json.dumps(receipt, separators=(',', ':')) + '\n')
        except OSError:
            # A telemetry filesystem failure cannot change a model request's
            # outcome or trigger a retry. No exception text/paths are printed.
            print('provider_receipt_write_failed', file=sys.stderr)

    def observed(*args, **kwargs):
        try:
            response = original(*args, **kwargs)
        except HTTPError as error:
            record(error.code, error.headers)
            raise
        record(getattr(response, 'status', 200), getattr(response, 'headers', None))
        return response

    with patch.object(provider, 'urlopen', observed):
        yield


def main() -> None:
    import socket
    import uvicorn

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt-file', type=Path, required=True)
    args = parser.parse_args()
    authority = Path('C:/Users/User/AppData/Local/Temp/opencode').resolve()
    output = args.receipt_file.resolve()
    if output.parent != authority or output.suffix != '.jsonl' or not authority.is_dir():
        parser.error('Use a JSONL file directly in the existing approved C: directory')
    with socket.socket() as connection:
        if connection.connect_ex(('127.0.0.1', 8001)) == 0:
            parser.error('Port8001 is occupied; verify ownership before restarting')
    with output.open('a', encoding='utf-8') as receipt:
        receipt.write(json.dumps({'kind': 'observer_start', 'at': datetime.now(UTC).isoformat(),
                                 'observer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                                 'observation_only': True}, separators=(',', ':')) + '\n')
    with observe_headers(output):
        uvicorn.run('game_discovery.api.main:app', host='127.0.0.1', port=8001, workers=1)


if __name__ == '__main__':
    main()
