"""Read-only evaluation summary. Does not score human relevance or call models."""
import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('journal', type=Path)
    args = parser.parse_args()
    data = json.loads(args.journal.read_text(encoding='utf-8'))
    for case in data['cases']:
        for turn in case['turns']:
            print(json.dumps({'case': case['id'], 'turn': turn['index']+1, 'status': turn['status']}, ensure_ascii=True))
            if turn['status'] != 200:
                for attempt in (turn.get('stored_event') or {}).get('attempts', []):
                    for trace in attempt['trace']:
                        print(json.dumps({k: v for k, v in trace.items() if k not in {'result', 'delivered'}}, ensure_ascii=True))
                        if 'delivered' in trace:
                            print(json.dumps({'delivered': trace['delivered']}, ensure_ascii=True))


if __name__ == '__main__':
    main()
