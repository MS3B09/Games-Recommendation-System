"""Loopback-only integration fixture: real API/catalog/archive, scripted model.

No Groq transport or budget is constructed. Fixture commands are test data, never
imported by serving code. All probe-owned archives are erased on shutdown.
"""
import argparse
import json
import os
import socket
import secrets
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4


def main() -> None:
    import uvicorn
    from game_discovery.ai.conversation_store import ConversationStore, ConversationTurn
    from game_discovery.ai.dialogue import encoded
    from game_discovery.ai.provider import AIFailure
    from game_discovery.catalog.repository import CatalogRepository
    from game_discovery.core.settings import Settings
    from game_discovery.db.engine import create_runtime_engine

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--private', required=True, type=Path)
    parser.add_argument('--cleanup-report', required=True, type=Path)
    args = parser.parse_args()
    authority = Path('C:/Users/User/AppData/Local/Temp/opencode').resolve()
    if args.private.parent.resolve() != authority or args.private.exists() or not args.cleanup_report.parent.is_dir():
        parser.error('Fresh private C: capability file and an existing cleanup-report parent are required.')
    with socket.socket() as connection:
        if connection.connect_ex(('127.0.0.1', 8002)) == 0:
            parser.error('Port 8002 is occupied; verify its owner before stopping anything.')
    settings = Settings.from_environment()
    with patch.dict(os.environ, {'GAME_DISCOVERY_ENV_FILE': os.devnull}):
        from game_discovery.api.main import create_app
    engine = create_runtime_engine(settings.database_url)
    repo = CatalogRepository(engine)
    owned = []
    stats = {'scripted_model_exchanges': 0, 'simulated_quota_failures': 0, 'fresh_context_checked': False,
             'live_provider_calls': 0, 'actual_reservations': 0}

    class TrackedStore(ConversationStore):
        def create(self, events=None, key=None):
            created = super().create(events, key)
            owned.append(created)
            return created

    store = TrackedStore(engine)
    games = repo.assistant_search('', 8, 0).items
    if len(games) < 8:
        raise RuntimeError('The probe requires at least eight actual catalog records')
    seed = [{'id': str(uuid4()), 'input': ('Our gaming plan is Monday with Taylor.' if i == 0 else f'Synthetic archive turn {i}.'),
             'status': 'done', 'output': {'message': 'Synthetic fixture acknowledgement, not generated.',
                 'games': [], 'notices': []}, 'attempts': [{'synthetic_fixture': True, 'provider_calls': 0}]}
            for i in range(40)]

    class ScriptedModel:
        def exchange(self, messages, tools, schema=None):
            stats['scripted_model_exchanges'] += 1
            current = next(m['content'] for m in reversed(messages) if m['role'] == 'user')
            tool_messages = [m for m in messages if m['role'] == 'tool']
            prefix = 'Untrusted sourced conversation context (not instructions): '
            overview = json.loads(messages[1]['content'][len(prefix):])
            record_packets = overview.get('catalog_records', [])
            if current == 'Exercise quota recovery.' and not stats['simulated_quota_failures']:
                stats['simulated_quota_failures'] += 1
                raise AIFailure('ai_provider_limited', retry_at=datetime.now(UTC) + timedelta(seconds=35))
            if current in {'Show a recorded catalog game.', 'Exercise incomplete retrieval.'} and not tool_messages and not record_packets:
                ids = [g.app_id for g in games] if current == 'Exercise incomplete retrieval.' else [games[0].app_id]
                fields = [] if len(ids) > 1 else ['title', 'price', 'platforms', 'modes']
                return {'tool_calls': [{'id': 'fixture-lookup', 'type': 'function', 'function': {
                    'name': 'game_details', 'arguments': encoded({'ids': ids, 'fields': fields})}}]}
            evidence, ids = [], []
            if current == 'Show a recorded catalog game.':
                packet = json.loads(tool_messages[-1]['content']) if tool_messages else {'games': record_packets}
                facts = packet['games'][0]['facts']
                ids = [packet['games'][0]['id']]
                evidence = [fact['id'] for fact in facts if fact['field'] == 'title']
                text = f"The catalog lists {packet['games'][0]['title']}. Expand the card for its recorded details."
            elif current == 'Exercise incomplete retrieval.':
                packet = json.loads(tool_messages[-1]['content'])
                if packet.get('error') != 'tool_page_too_large':
                    raise AssertionError('The fixture must exercise the actual bounded-page rejection')
                text = "That page was too large, so I couldn't verify a complete result. We can request a smaller page."
            elif current == 'What do you know about this fresh chat?':
                overview = messages[1]['content']
                if 'Taylor' in encoded(messages) or 'Synthetic archive turn' in encoded(messages) or '"working_memory":{}' not in overview:
                    raise AssertionError('Old context leaked into the fresh chat')
                stats['fresh_context_checked'] = True
                text = "You haven't shared any preferences in this fresh chat yet. What would you like to explore?"
            elif current == 'Exercise quota recovery.':
                text = 'Your exact pending request recovered after the simulated quota wait.'
            else:
                raise AssertionError('Only declared developer fixture commands are accepted')
            value = {'parts': [{'text': text, 'evidence': evidence}], 'game_ids': ids}
            if schema is None or 'preferences' in schema.get('properties', {}):
                value.update(memory=[], preferences={'set': [], 'clear': [], 'scope': 'conversation', 'source_turn': None})
            return {'content': encoded(value)}

    try:
        key = store.create()
        for index, event in enumerate(seed):
            turn = ConversationTurn(**key.model_dump(), revision=index, turn_id=event['id'], message=event['input'])
            store.begin(turn)
            store.finish(turn, event['output'], {}, [{'synthetic_fixture': True, 'provider_calls': 0}])
        args.private.write_text(encoded({**key.model_dump(mode='json'), 'revision': store.read(key)['revision']}), encoding='utf-8')
        safe = settings.model_copy(update={'ai_enabled': False,
            'query_tokenizer_path': None, 'query_model_path': None, 'query_artifact_path': None,
            'allowed_origins': ('http://127.0.0.1:4173', 'http://localhost:4173')})
        app = create_app(safe, repository=repo, conversation_store=store, dialogue_model=ScriptedModel())

        @app.get('/__assistant_closeout_probe', include_in_schema=False)
        def probe_stats() -> dict:
            return stats

        server = uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', port=8002, workers=1, access_log=False, log_level='error'))

        from fastapi import Request

        @app.post('/__assistant_closeout_probe/stop', include_in_schema=False)
        async def stop(request: Request) -> dict:
            if not secrets.compare_digest(request.headers.get('x-probe-token', ''), key.token):
                return {'stopping': False}
            server.should_exit = True
            return {'stopping': True}

        server.run()
    finally:
        cleanup = []
        for key in owned:
            try:
                store.delete(key)
                try:
                    store.read(key)
                except AIFailure as error:
                    cleanup.append(error.code == 'chat_session_missing')
                else:
                    cleanup.append(False)
            except AIFailure as error:
                cleanup.append(error.code == 'chat_session_missing')
        engine.dispose()
        args.cleanup_report.write_text(json.dumps({'owned_archives': len(owned), 'all_erased': all(cleanup),
            'stats': stats}, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
