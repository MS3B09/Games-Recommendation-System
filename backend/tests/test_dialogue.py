"""New architecture mechanics, diverse transcripts and long archive retrieval.

Scripted provider tests are NOT evidence of real LLM conversation quality.
"""
import copy
import json
import unittest
from io import BytesIO
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError
from uuid import uuid4

from fastapi.testclient import TestClient

from game_discovery.ai.conversation_store import ConversationKey, ConversationTurn
from game_discovery.ai.dialogue import Dialogue, DialogueAnswer, TOOLS, compact_schema
from game_discovery.ai.provider import AIFailure, GroqAssistant
from game_discovery.catalog.repository import CatalogFailure, GamePage
from game_discovery.core.settings import Settings
from test_chat_rag import game, repository


class MemoryArchive:
    def __init__(self):
        self.rows = {}

    def create(self, events=None, key=None):
        key = key or ConversationKey(conversation_id=uuid4(), token='a' * 43)
        self.rows[str(key.conversation_id)] = {'token': key.token, 'revision': len(events or []),
            'document': {'events': copy.deepcopy(events or []), 'memory': {}}}
        return key

    def read(self, key):
        row = self.rows.get(str(key.conversation_id))
        if row is None or row['token'] != key.token:
            raise AIFailure('chat_session_missing')
        return copy.deepcopy(row)

    def begin(self, turn):
        row = self.read(turn)
        if row['revision'] != turn.revision:
            raise AIFailure('chat_session_conflict')
        row['document']['events'].append({'id': str(turn.turn_id), 'input': turn.message, 'status': 'pending', 'attempts': []})
        self.rows[str(turn.conversation_id)] = row
        return copy.deepcopy(row)

    def finish(self, turn, result, memory, trace):
        row = self.rows[str(turn.conversation_id)]
        event = row['document']['events'][-1]
        event.update(status='done' if result else 'failed', output=copy.deepcopy(result))
        event['attempts'].append(copy.deepcopy(trace))
        if result:
            row['document']['memory'] = copy.deepcopy(memory)
            row['revision'] += 1

    def delete(self, key):
        self.read(key)
        del self.rows[str(key.conversation_id)]
        return True


def reply(value):
    return {'role': 'assistant', 'content': json.dumps(value)}


def answer(text='Hello! What would you like to chat about?', ids=None, evidence=None, memory=None):
    return reply({'parts': [{'text': text, 'evidence': evidence or []}],
        'game_ids': ids or [], 'memory': memory or []})


def tools(*calls):
    return {'role': 'assistant', 'content': None, 'tool_calls': [
        {'id': f'call-{i}', 'type': 'function', 'function': {'name': name, 'arguments': json.dumps(args)}}
        for i, (name, args) in enumerate(calls)]}


class DialogueTests(unittest.TestCase):
    def setUp(self):
        self.archive = MemoryArchive()
        self.key = self.archive.create()
        self.repo = repository([game(10, 'One', ['single-player']), game(20, 'Two', ['online-co-op'])])
        self.repo.assistant_search.side_effect = lambda query, limit, offset: GamePage(
            catalog_version='fixture', items=[game(10, 'One'), game(20, 'Two')][offset:offset+limit], total=2, offset=offset)
        self.model = MagicMock()

    def turn(self, message, outputs):
        turn = ConversationTurn(**self.key.model_dump(), turn_id=uuid4(),
                                revision=self.archive.read(self.key)['revision'], message=message)
        scripted = iter(outputs)
        def exchange(messages, active_tools, schema=None):
            response = next(scripted)
            if isinstance(response, Exception):
                raise response
            if schema and {'memory', 'preferences'} - schema['properties'].keys():
                # Search scope is already retained by the server.
                response = copy.deepcopy(response)
                content = response.get('content')
                if content:
                    value = json.loads(content)
                    excluded = {'memory', 'preferences'} - schema['properties'].keys()
                    response = {'content': json.dumps({k: v for k, v in value.items() if k not in excluded})}
            return response
        self.model.exchange.side_effect = exchange
        return Dialogue(self.model, self.repo, self.archive, None).run(turn, self.archive.begin(turn))

    def test_natural_chat_has_one_call_no_classifier_and_no_catalog_access(self):
        text = "I'm Current's game-discovery assistant. What would you like to play?"
        result = self.turn("Hello, what's your name?", [answer(text)])
        self.assertEqual(result['message'], text)
        self.assertFalse(self.repo.mock_calls)
        self.assertEqual(self.model.exchange.call_count, 1)
        self.assertTrue(self.model.exchange.call_args.args[1])
        result = self.turn('Which GPT model and architecture exactly?', [answer(
            "I don't share implementation details. I'm here to help you find games that fit your taste.")])
        self.assertNotIn('GPT', result['message'])
        general = '**For fluffier rice**, rinse it first. If you want a cooking-themed game afterward, I can help you find one.'
        result = self.turn('How do I make rice fluffier?', [answer(general)])
        self.assertEqual(result['message'], general)
        self.assertEqual(self.model.exchange.call_count, 3)
        self.assertFalse(self.repo.mock_calls)

    def test_direct_reply_finishes_without_a_competing_native_reply_tool(self):
        payload = json.loads(answer('Hi! Want to tell me about your day?')['content'])
        result = self.turn('Hello', [reply(payload)])
        self.assertEqual({t['function']['name'] for t in TOOLS}, {
            'recommend_games', 'lookup_titles', 'game_details', 'conversation_history'})
        self.assertIn('your day', result['message'])
        self.assertEqual(self.model.exchange.call_count, 1)
        self.assertFalse(self.repo.mock_calls)

    def test_natural_reply_may_omit_empty_metadata_without_inferred_edits(self):
        for metadata in ({}, {'preferences': {}}, {'preferences': None}):
            result = self.turn('Let us just chat', [reply({
                'parts': [{'text': 'Of course. What is on your mind?'}], **metadata})])
            self.assertIn('What is on your mind', result['message'])
            self.assertEqual(result['games'], [])
            self.assertIsNone(result['preference_changes'])
            self.assertEqual(self.archive.read(self.key)['document']['memory'], {})
        for invalid in ([], False, 'none'):
            with self.assertRaises(ValueError):
                self.turn('Let us just chat', [reply({'parts': [{'text': 'Hello.'}], 'preferences': invalid})])
        self.assertFalse(self.repo.mock_calls)

    def test_plain_native_response_needs_no_formatting_call_or_guessed_edits(self):
        result = self.turn('A friend might join on Tuesday; no budget is agreed.', [
            {'role': 'assistant', 'content': 'Tuesday is tentative, with no agreed budget.'}])
        self.assertEqual(result['message'], 'Tuesday is tentative, with no agreed budget.')
        self.assertEqual(self.model.exchange.call_count, 1)
        self.assertFalse(self.repo.mock_calls)
        self.assertIsNone(result['applied_filters'])
        self.assertIsNone(result['preference_changes'])
        self.assertEqual(self.archive.read(self.key)['document']['memory'], {})
        self.assertIn('Tuesday', self.archive.read(self.key)['document']['events'][0]['input'])
        self.turn('Inspect One.', [tools(('game_details', {'ids': [10], 'finish': True})),
                                  answer('One is recorded.', [10], ['game:10:title'])])
        followup = self.turn('Does absent support prove incompatibility?', [
            {'role': 'assistant', 'content': 'No. Missing support is unknown.'}])
        self.assertEqual(followup['games'], [])
        with self.assertRaises(ValueError):
            self.turn('Inspect One again.', [tools(('game_details', {'ids': [10], 'finish': True})),
                {'role': 'assistant', 'content': 'Unsupported unstructured game facts.'}])
        self.assertEqual(self.archive.read(self.key)['document']['events'][-1]['status'], 'failed')

    def test_broad_search_then_details_and_comparison_are_two_finite_tool_rounds(self):
        result = self.turn('Find that series and tell me how its games differ.', [
            tools(('lookup_titles', {'query': 'One', 'limit': 2})),
            tools(('game_details', {'ids': [10, 20], 'fields': ['title', 'modes']})),
            answer('One records single-player; Two records online co-op.', [10, 20], ['game:10:modes', 'game:20:modes'])])
        self.assertEqual([c['game']['app_id'] for c in result['games']], [10, 20])
        self.assertEqual(self.model.exchange.call_count, 3)
        self.assertEqual(self.model.exchange.call_args.args[1], [])
        self.assertIsNotNone(self.model.exchange.call_args.args[2])
        records = self.archive.read(self.key)['document']['events']
        self.assertEqual(len([t for t in records[0]['attempts'][0] if 'tool' in t]), 2)
        self.assertEqual(records[0]['output']['games'][0]['game']['title'], 'One')

    def test_small_followup_does_not_overflow_from_duplicate_cached_and_tool_evidence(self):
        self.turn('Show both games', [tools(('lookup_titles', {'query': 'games'})),
            answer('Here are One and Two.', [10, 20], ['game:10:title', 'game:20:title'])])
        result = self.turn('How do their modes and platforms differ?', [
            tools(('game_details', {'ids': [10, 20], 'fields': ['modes', 'platforms']})),
            answer('Here are their recorded modes.', [10, 20], ['game:10:modes', 'game:20:modes'])])
        self.assertEqual(len(result['games']), 2)
        self.assertEqual(self.archive.read(self.key)['revision'], 2)

    def test_search_scope_never_means_franchise_or_catalog_completeness(self):
        dialogue = Dialogue(self.model, self.repo, self.archive, None)
        packet = dialogue.tool('lookup_titles', {'query': 'One', 'offset': 1, 'limit': 1}, {'events': [], 'memory': {}}, 's')
        self.assertEqual(packet['total_matches'], 2)
        self.assertFalse(packet['returned_all_matches'])
        self.assertFalse(packet['franchise_completeness_established'])
        self.assertEqual(packet['offset'], 1)

    def test_recommendation_resolves_named_exclusions_without_model_lookup_rounds(self):
        schema = next(t['function']['parameters'] for t in TOOLS if t['function']['name'] == 'recommend_games')
        self.assertIn('excluded_titles', schema['required'])
        self.assertIn('ambiguous names unchanged', schema['properties']['excluded_titles']['description'])
        self.repo = repository([game(10, 'One'), game(20, 'Two'), game(30, 'Three')])
        result = self.turn('Recommend an alternative to One and Two.', [
            tools(('recommend_games', {'save_as_normal': False, 'query': 'games', 'filters': {},
                                      'excluded_titles': ['One', 'Two'], 'finish': True})),
            answer('Three is a catalog option.', [30], ['game:30:title'])])
        self.assertEqual(self.model.exchange.call_count, 2)
        self.assertEqual(result['applied_filters']['excluded_ids'], [10, 20])
        self.assertEqual([c['game']['app_id'] for c in result['games']], [30])
        self.assertEqual(self.repo.chat_title.call_count, 2)
        self.assertEqual(self.repo.chat_candidates.call_count, 1)
        self.assertEqual(self.archive.read(self.key)['document']['memory'], {})
        self.repo = repository([game(10, 'One'), game(11, 'One Again'), game(30, 'Three')])
        dialogue = Dialogue(self.model, self.repo, self.archive, None)
        args = {'save_as_normal': False, 'query': 'games', 'filters': {}, 'excluded_titles': ['On']}
        packet = dialogue.tool('recommend_games', args, {}, 'ambiguous')
        self.assertEqual(packet['error'], 'exclusion_needs_clarification')
        self.assertEqual({g['id'] for g in packet['options']}, {10, 11})
        self.repo.chat_candidates.assert_not_called()
        self.assertIsNone(dialogue.search_preferences)
        clarification = self.turn('Exclude On and recommend an alternative.', [
            tools(('recommend_games', args)),
            {'content': 'Did you mean One or One Again?'}])
        self.assertEqual(clarification['message'], 'Did you mean One or One Again?')
        self.assertEqual(clarification['games'], [])
        self.assertIsNone(clarification['preference_changes'])
        self.assertEqual(self.archive.read(self.key)['document']['memory'], {})
        self.repo.chat_candidates.assert_not_called()
        args['excluded_titles'] = ['Not in this catalog']
        packet = dialogue.tool('recommend_games', args, {}, 'absent')
        self.assertEqual(packet['excluded_titles'][0]['outcome'], 'not_in_catalog')
        self.assertEqual(packet['applied_filters'], {})
        self.turn('Save One as an exclusion.', [reply({'parts': [{'text': 'Noted.'}],
            'preferences': {'set': [{'field': 'excluded_ids', 'value': [10]}]}})])
        result = self.turn('Add Three to my normal exclusions and recommend another game.', [
            tools(('recommend_games', {'save_as_normal': True, 'query': 'games', 'filters': {},
                                      'excluded_titles': ['Three'], 'finish': True})),
            answer('One Again is a catalog option.', [11], ['game:11:title'])])
        self.assertEqual(result['applied_filters']['excluded_ids'], [10, 30])
        self.assertEqual(self.archive.read(self.key)['document']['memory']['_catalog_requirements']['filters']['excluded_ids'], [10, 30])
        self.repo.chat_title.side_effect = CatalogFailure('catalog_unavailable')
        self.repo.chat_candidates.reset_mock()
        dialogue = Dialogue(self.model, self.repo, self.archive, None)
        packet = dialogue.tool('recommend_games', args, {}, 'unavailable')
        self.assertEqual(packet['error'], 'exclusion_lookup_unavailable')
        self.repo.chat_candidates.assert_not_called()
        self.assertIsNone(dialogue.search_preferences)

    def test_any_game_details_and_description_continuation_are_accessible(self):
        original = game(10, 'One', description='z' * 5000)
        self.repo.resolve.return_value = None
        self.repo = repository([original])
        dialogue = Dialogue(self.model, self.repo, self.archive, None)
        packet = dialogue.tool('game_details', {'ids': [10], 'fields': ['description', 'eligibility'],
                               'description_offset': 2000, 'description_limit': 1000}, {}, 'd')
        description = packet['games'][0]['facts'][0]['value']
        self.assertEqual(description['offset'], 2000)
        self.assertEqual(description['next_offset'], 3000)
        self.assertIn('evidence', packet['games'][0]['available_fields'])

    def test_large_evidence_values_are_losslessly_paged_instead_of_silently_omitted(self):
        original = game(10, 'One', description='long catalog evidence ' * 500)
        dialogue = Dialogue(self.model, repository([original]), self.archive, None)
        chunks = []
        offset = 0
        while True:
            packet = dialogue.tool('game_details', {'ids': [10], 'fields': ['evidence'],
                'value_offset': offset, 'value_limit': 500}, {}, 'd')
            value = packet['games'][0]['facts'][0]['value']
            self.assertEqual(value['encoding'], 'json')
            chunks.append(value['excerpt'])
            if value['next_offset'] is None:
                break
            self.assertFalse(value['returned_all_field'])
            offset = value['next_offset']
        restored = json.loads(''.join(chunks))
        self.assertEqual(restored, original.model_dump(mode='json')['evidence'])

    def test_unresolved_source_and_card_invention_fail_atomically(self):
        for output in (answer('Unsupported fact', evidence=['invented']), answer('Invented title', [999])):
            with self.subTest(output=output), self.assertRaises(AIFailure):
                self.turn('Tell me something', [output])
            self.assertEqual(self.archive.read(self.key)['document']['events'][-1]['status'], 'failed')

    def test_tool_argument_errors_are_given_to_model_without_executing_them(self):
        result = self.turn('Can you check?', [tools(('game_details', {'ids': ["DROP TABLE games"]})),
                                            answer('Which game would you like me to check?')])
        self.assertIn('Which game', result['message'])
        self.repo.resolve.assert_not_called()
        self.assertIn('invalid_tool_arguments', self.model.exchange.call_args.args[0][-1]['content'])

    def test_tool_bound_stops_before_extra_reads(self):
        with self.assertRaises(AIFailure):
            self.turn('Read everything', [tools(*[('lookup_titles', {})] * 5)])
        self.repo.assistant_search.assert_not_called()

    def test_long_session_keeps_every_original_and_recalls_old_correction(self):
        row = self.archive.rows[str(self.key.conversation_id)]
        row['document']['events'] = [{'id': str(uuid4()), 'input': 'My platform is Linux.' if i == 0 else f'Unrelated exchange {i}',
            'status': 'done', 'output': {'message': 'Understood.', 'games': []}, 'attempts': []} for i in range(180)]
        row['revision'] = 180
        row['document']['memory'] = {'platform': {'value': 'Linux', 'source_turn': row['document']['events'][0]['id']}}
        result = self.turn('Actually, I use Windows now; forget that old platform preference.', [answer(
            'Got it—Windows replaces the earlier Linux preference.', memory=[{'key': 'platform', 'value': 'Windows'}])])
        self.assertIn('Windows', result['message'])
        row = self.archive.read(self.key)
        self.assertEqual(len(row['document']['events']), 181)
        self.assertEqual(row['document']['events'][0]['input'], 'My platform is Linux.')
        self.assertEqual(row['document']['memory']['platform']['value'], 'Windows')
        result = self.turn('What did I originally tell you?', [tools(('conversation_history', {'query': 'My platform is Linux'})),
            answer('Originally you told me Linux; you later corrected it to Windows.')])
        packet = json.loads(self.model.exchange.call_args.args[0][-1]['content'])
        self.assertEqual(packet['total_matches'], 1)
        self.assertIn('Originally', result['message'])

    def test_history_citations_are_valid_for_user_memory_not_catalog_card_evidence(self):
        self.turn('We will play on Sunday.', [answer('Noted.')])
        origin = self.archive.read(self.key)['document']['events'][0]['id']
        result = self.turn('Which day did I say?', [tools(('conversation_history', {'query': 'Sunday'})),
            answer('You said Sunday.', evidence=[origin])])
        self.assertEqual(result['evidence'][0]['scope'], 'user_conversation_only_not_game_facts')

    def test_working_memory_can_cite_its_original_user_without_an_unneeded_catalog_read(self):
        self.turn('My friend is Alex.', [answer('Noted.', memory=[{'key': 'friend', 'value': 'Alex'}])])
        origin = self.archive.read(self.key)['document']['events'][0]['id']
        payload = {'parts': [{'text': 'Your friend is Alex.', 'evidence': [origin]}]}
        result = self.turn('What is my friend called?', [reply(payload)])
        self.assertEqual(result['message'], 'Your friend is Alex.')
        self.assertEqual(self.model.exchange.call_count, 2)  # first acknowledgement + this reply
        self.assertFalse(self.repo.mock_calls)

    def test_failed_user_statement_is_preserved_in_context_with_its_original_memory_source(self):
        with self.assertRaises(AIFailure):
            self.turn('My platform is Linux.', [AIFailure('ai_timeout')])
        original = self.archive.read(self.key)['document']['events'][0]['id']
        self.turn('What platform did I tell you?', [answer('You told me Linux.', memory=[
            {'key': 'platform', 'value': 'Linux', 'source_turn': original}])])
        context = self.model.exchange.call_args.args[0]
        self.assertTrue(any(m['role'] == 'user' and m['content'] == 'My platform is Linux.' for m in context))
        self.assertEqual(self.archive.read(self.key)['document']['memory']['platform']['source_turn'], original)

    def test_new_chat_is_independent_and_does_not_inherit_main_or_previous_inputs(self):
        self.turn('I use Linux.', [answer('Noted.', memory=[{'key': 'platform', 'value': 'Linux'}])])
        other = self.archive.create()
        turn = ConversationTurn(**other.model_dump(), turn_id=uuid4(), revision=0, message='What do you know about me?')
        self.model.exchange.side_effect = [answer('You have not shared any preferences in this chat yet.')]
        Dialogue(self.model, self.repo, self.archive, None).run(turn, self.archive.begin(turn))
        context = json.dumps(self.model.exchange.call_args.args[0][1:])
        self.assertNotIn('Linux', context)
        self.assertNotIn('favorite_ids', context)
        self.assertEqual(self.archive.read(other)['document']['memory'], {})

    def test_general_conversation_has_no_legacy_intent_word_blacklist(self):
        result = self.turn('For vocabulary practice, respond only with the word social.', [answer('social')])
        self.assertEqual(result['message'], 'social')
        self.assertFalse(self.repo.mock_calls)

    def test_context_is_bounded_but_original_large_messages_are_not_changed(self):
        row = self.archive.rows[str(self.key.conversation_id)]
        row['document']['events'] = [{'id': str(uuid4()), 'input': '🎮' * 1000,
            'status': 'done', 'output': {'message': '🎮' * 1000, 'games': []}, 'attempts': []} for _ in range(40)]
        row['revision'] = 40
        self.turn('Hello again', [answer('Hello!')])
        self.assertEqual(len(self.archive.read(self.key)['document']['events']), 41)
        self.assertIn('omitted', self.model.exchange.call_args.args[0][1]['content'])

    def test_native_tool_and_final_schemas_fit_existing_per_call_byte_budget(self):
        dialogue = Dialogue(self.model, self.repo, self.archive, None)
        turn = ConversationTurn(**self.key.model_dump(), turn_id=uuid4(), revision=0, message='x' * 2000)
        messages = dialogue.context({'events': [], 'memory': {}}, turn)
        Dialogue.fit(messages, TOOLS, None)
        Dialogue.fit(messages, [], compact_schema(DialogueAnswer, strict=True))

    def test_native_tool_enum_contracts_are_inline_and_not_hidden_behind_refs(self):
        self.assertNotIn('$ref', json.dumps(TOOLS))
        rec = next(t['function']['parameters'] for t in TOOLS if t['function']['name'] == 'recommend_games')
        filters = rec['properties']['filters']['properties']
        self.assertEqual(filters['platforms']['items']['enum'], ['windows', 'mac', 'linux'])
        self.assertIn('online-co-op', filters['required_modes']['items']['enum'])
        self.assertIn('save_as_normal', rec['required'])
        self.assertIn('query', rec['required'])
        self.assertIn('filters', rec['required'])
        self.assertIn('not only in query', rec['properties']['filters']['description'])
        self.assertEqual(rec['properties']['save_as_normal']['type'], 'boolean')
        for missing in ('query', 'filters', 'save_as_normal'):
            args = {'save_as_normal': False, 'query': 'cooperative games', 'filters': {'required_modes': ['online-co-op']}}
            del args[missing]
            with self.assertRaises(ValueError):
                Dialogue(self.model, self.repo, self.archive, None).tool('recommend_games', args, {}, 'required')
        self.repo.chat_candidates.assert_not_called()

    def test_recommendations_default_to_ready_but_metadata_tools_require_readiness(self):
        for tool in TOOLS:
            function = tool['function']
            with self.subTest(name=function['name']):
                if function['name'] == 'recommend_games':
                    self.assertNotIn('finish', function['parameters']['required'])
                    self.assertIn('Defaults to true', function['parameters']['properties']['finish']['description'])
                else:
                    self.assertIn('finish', function['parameters']['required'])
                self.assertEqual(function['parameters']['properties']['finish']['type'], 'boolean')

    def test_reply_schema_constrains_citations_and_cards_to_known_identifiers(self):
        dialogue = Dialogue(self.model, self.repo, self.archive, None)
        dialogue.sources['game:10:modes'] = {'id': 'game:10:modes', 'value': ['single-player']}
        dialogue.games[10] = game(10, 'One')
        schema = dialogue.reply_schema()
        self.assertEqual(schema['$defs']['Passage']['properties']['evidence']['items']['enum'], ['game:10:modes'])
        self.assertEqual(schema['properties']['game_ids']['items']['enum'], [10])

    def test_history_pagination_aliases_do_not_trigger_hidden_catalog_reads(self):
        document = {'memory': {}, 'events': [{'id': str(uuid4()), 'input': 'Our original plan is Tuesday.',
            'status': 'done', 'output': {'message': 'Noted.', 'games': []}}]}
        dialogue = Dialogue(self.model, self.repo, self.archive, None)
        for field in ('limit', 'max_results'):
            packet = dialogue.tool('conversation_history', {field: 1}, document, 'h')
            self.assertEqual(packet['entries'][0]['user'], 'Our original plan is Tuesday.')
        self.assertFalse(self.repo.mock_calls)

    def test_history_search_finds_original_and_corrected_memory_key_values(self):
        self.turn('We plan for Tuesday.', [answer('Noted.', memory=[{'key': 'plan_day', 'value': 'Tuesday'}])])
        self.turn('Change that to Thursday.', [answer('Updated.', memory=[{'key': 'plan_day', 'value': 'Thursday'}])])
        document = self.archive.read(self.key)['document']
        packet = Dialogue(self.model, self.repo, self.archive, None).tool('conversation_history',
            {'query': 'plan_day', 'max_results': 10}, document, 'h')
        self.assertEqual([e['memory_changes'][0]['value'] for e in packet['entries']], ['Tuesday', 'Thursday'])
        self.assertEqual(document['events'][0]['input'], 'We plan for Tuesday.')

    def test_invalid_citation_fails_without_an_automatic_repair_call(self):
        with self.assertRaises(AIFailure):
            self.turn('Inspect One.', [tools(('game_details', {'ids': [10], 'fields': ['modes']})),
                answer('One records single-player.', [10], ['game:10:modes includes single-player'])])
        self.assertEqual(self.model.exchange.call_count, 2)
        self.assertEqual(self.archive.read(self.key)['document']['events'][-1]['status'], 'failed')

    def test_groq_native_tools_never_combine_with_incompatible_json_mode(self):
        budget = MagicMock()
        budget.reserve.return_value = True
        model = GroqAssistant(Settings(), budget)
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({'choices': [{'message': answer()}]}).encode()
        with patch('game_discovery.ai.provider.urlopen', return_value=response) as network:
            model.exchange([{'role': 'user', 'content': 'Hi'}], TOOLS)
            payload = json.loads(network.call_args.args[0].data)
            self.assertNotIn('response_format', payload)
            self.assertEqual(payload['tool_choice'], 'auto')
            self.assertLessEqual(budget.reserve.call_args.args[0], 13280)
            model.exchange([{'role': 'user', 'content': 'Hi'}], [], compact_schema(DialogueAnswer, strict=True))
            self.assertEqual(json.loads(network.call_args.args[0].data)['response_format']['type'], 'json_schema')

    def test_proposed_declared_call_is_locally_validated_without_a_hidden_http_retry(self):
        budget = MagicMock()
        budget.reserve.return_value = True
        model = GroqAssistant(Settings(), budget)
        proposal = {'name': 'game_details', 'arguments': {'ids': [10], 'fields': ['title'], 'finish': True}}
        error = HTTPError('https://provider.invalid', 400, 'validation', {}, BytesIO(json.dumps(
            {'error': {'code': 'tool_use_failed', 'failed_generation': json.dumps(proposal)}}).encode()))
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({'choices': [{'message':
            answer('One is in the catalog.', [10], ['game:10:title'])}]}).encode()
        turn = ConversationTurn(**self.key.model_dump(), turn_id=uuid4(), revision=0, message='Look up One.')
        with patch('game_discovery.ai.provider.urlopen', side_effect=[error, response]) as network:
            result = Dialogue(model, self.repo, self.archive, None).run(turn, self.archive.begin(turn))
        self.assertEqual(result['message'], 'One is in the catalog.')
        self.assertEqual(network.call_count, 2)
        self.assertEqual(budget.reserve.call_count, 2)
        trace = self.archive.read(self.key)['document']['events'][0]['attempts'][0]
        self.assertEqual(trace[0]['provider_rejected_proposal']['provider_code'], 'tool_use_failed')
        self.assertGreater(model.last_reserved_units, 0)
        self.repo.resolve.assert_called_once_with([10])

    def test_unknown_proposed_function_cannot_be_recovered_or_executed(self):
        for name in ('run_shell', 'json'):
            model = GroqAssistant(Settings(), MagicMock())
            body = {'error': {'code': 'tool_use_failed', 'failed_generation': json.dumps(
                {'name': name, 'arguments': {'parts': [{'text': 'Undeclared reply tool.'}]}})}}
            error = HTTPError('https://provider.invalid', 400, 'validation', {}, BytesIO(json.dumps(body).encode()))
            with patch('game_discovery.ai.provider.urlopen', side_effect=error) as network, self.assertRaises(AIFailure):
                model.exchange([{'role': 'user', 'content': 'Hello'}], TOOLS)
            self.assertEqual(network.call_count, 1)

    def test_rejected_final_json_uses_local_guards_without_retry_or_losing_temporary_scope(self):
        self.turn('Keep a normal budget.', [reply({
            'parts': [{'text': 'Noted.'}], 'preferences': {'set': [{'field': 'max_price_cents', 'value': 1000}]}})])
        for invalid in (None, 'source', 'card', 'preference'):
            with self.subTest(invalid=invalid):
                payload = json.loads(answer('One is recorded as single-player.', [10], ['game:10:modes'])['content'])
                payload['preferences'] = {'scope': 'turn', 'set': [{'field': 'max_price_cents', 'value': 3000}], 'clear': []}
                rejected = copy.deepcopy(payload)
                if invalid == 'source':
                    rejected['parts'][0]['evidence'] = ['invented']
                elif invalid == 'card':
                    rejected['game_ids'] = [999]
                elif invalid == 'preference':
                    rejected['preferences'] = {'scope': 'forever'}
                responses = []
                for message in (tools(('game_details', {'ids': [10], 'fields': ['modes'], 'finish': True})),):
                    response = MagicMock()
                    response.__enter__.return_value.read.return_value = json.dumps({'choices': [{'message': message}]}).encode()
                    responses.append(response)
                body = {'error': {'code': 'json_validate_failed', 'failed_generation': json.dumps(rejected)}}
                responses.append(HTTPError('https://provider.invalid', 400, 'validation', {}, BytesIO(json.dumps(body).encode())))
                budget = MagicMock()
                budget.reserve.return_value = True
                model = GroqAssistant(Settings(), budget)
                turn = ConversationTurn(**self.key.model_dump(), turn_id=uuid4(),
                    revision=self.archive.read(self.key)['revision'], message='For this turn only, allow 3000 cents.')
                with patch('game_discovery.ai.provider.urlopen', side_effect=responses) as network:
                    if invalid:
                        with self.assertRaises((AIFailure, ValueError)):
                            Dialogue(model, self.repo, self.archive, None).run(turn, self.archive.begin(turn))
                    else:
                        result = Dialogue(model, self.repo, self.archive, None).run(turn, self.archive.begin(turn))
                        self.assertEqual(result['preference_changes']['scope'], 'turn')
                self.assertEqual(network.call_count, 2)
                self.assertEqual(budget.reserve.call_count, 2)
                self.assertEqual(self.archive.read(self.key)['document']['memory']['_catalog_requirements']['filters']['max_price_cents'], 1000)

    def test_supported_catalog_reply_finishes_without_a_critique_call(self):
        result = self.turn('Tell me the recorded modes of One.', [
            tools(('game_details', {'ids': [10], 'fields': ['modes']})),
            answer('One records single-player.', [10], ['game:10:modes'])])
        self.assertEqual(result['message'], 'One records single-player.')
        self.assertNotIn('unsupported_claims', result)
        self.assertEqual(self.model.exchange.call_count, 2)
        trace = self.archive.read(self.key)['document']['events'][-1]['attempts'][0]
        self.assertEqual(len([t for t in trace if 'model_call' in t]), 2)

    def test_unseen_original_history_id_cannot_be_used_as_supplied_evidence(self):
        dialogue = Dialogue(self.model, self.repo, self.archive, None)
        original = str(uuid4())
        dialogue.history_sources[original] = {'id': original, 'value': {'user': 'Something long ago.'}}
        with self.assertRaises(AIFailure):
            dialogue.validate_answer(DialogueAnswer.model_validate(json.loads(answer(evidence=[original])['content'])))

    def test_identifier_assertions_need_identifier_field_evidence_not_just_a_title(self):
        dialogue = Dialogue(self.model, self.repo, self.archive, None)
        dialogue.game_packet(game(10, 'One'), ['title'])
        candidate = json.loads(answer('One (ID 10) is in the catalog.', [10], ['game:10:title'])['content'])
        with self.assertRaises(AIFailure):
            dialogue.validate_answer(DialogueAnswer.model_validate(candidate))
        dialogue.game_packet(game(10, 'One'), ['app_id'])
        candidate['parts'][0]['evidence'].append('game:10:app_id')
        dialogue.validate_answer(DialogueAnswer.model_validate(candidate))

    def test_price_and_observation_date_cannot_be_fabricated_behind_a_valid_source_id(self):
        dialogue = Dialogue(self.model, self.repo, self.archive, None)
        original = game(10, 'One')
        dialogue.game_packet(original, ['price', 'title'])
        price = original.price.amount_cents / 100
        date = original.price.observed_at.date().isoformat()
        for text, evidence in ((f'Recorded ${price:.2f} USD on {date}.', ['game:10:price']),
                               ('Recorded $9876.54 USD.', ['game:10:price']),
                               (f'Recorded ${price:.2f} on 1999‑11‑15.', ['game:10:price']),
                               (f'Recorded ${price:.2f} USD.', ['game:10:title'])):
            candidate = DialogueAnswer.model_validate(json.loads(answer(text, [10], evidence)['content']))
            if evidence == ['game:10:price'] and date in text:
                dialogue.validate_answer(candidate)
            else:
                with self.assertRaises(AIFailure):
                    dialogue.validate_answer(candidate)

    def test_temporary_budget_in_fact_reply_is_not_misclassified_as_a_game_price(self):
        original = game(10, 'One')
        price = original.price.amount_cents / 100
        payload = json.loads(answer(f'With a temporary budget of $36, One records ${price:.2f} USD.',
                                   [10], ['game:10:price'])['content'])
        payload['preferences'] = {'scope': 'turn', 'set': [{'field': 'max_price_cents', 'value': 3600}]}
        result = self.turn('For this turn only, allow 36 USD.', [
            tools(('game_details', {'ids': [10], 'fields': ['price']})), reply(payload)])
        self.assertEqual(result['preference_changes']['scope'], 'turn')
        self.assertNotIn('_catalog_requirements', self.archive.read(self.key)['document']['memory'])

    def test_price_provenance_stays_in_cards_or_in_text_when_no_card_is_available(self):
        dialogue = Dialogue(self.model, self.repo, self.archive, None)
        original = game(10, 'One')
        dialogue.game_packet(original, ['price'])
        payload = json.loads(answer(f'One costs ${original.price.amount_cents / 100:.2f} USD.', evidence=['game:10:price'])['content'])
        part = DialogueAnswer.model_validate(payload).parts[0]
        date = original.price.observed_at.date().isoformat()
        rendered = dialogue.render_part(part)
        self.assertIn(date, rendered)
        self.assertIn('recorded US/USD', rendered)
        self.assertEqual(dialogue.render_part(part, [10]), part.text)
        self.assertIn(date, dialogue.render_part(part, [20]))
        part.text = f'Recorded USD price observed on {date}.'
        self.assertEqual(dialogue.render_part(part), part.text)
        text = f'One is recorded at ${original.price.amount_cents / 100:.2f} USD.'
        result = self.turn('Recommend One and tell me its recorded price.', [
            tools(('recommend_games', {'save_as_normal': False, 'query': 'One', 'filters': {}, 'limit': 1})),
            answer(text, [10], ['game:10:price'])])
        self.assertEqual(result['message'], text)
        self.assertEqual(result['games'][0]['game']['price'], original.price.model_dump(mode='json'))
        self.assertIn('not live quotes', result['notices'][0])

    def test_reply_validation_does_not_spend_a_call_repairing_invented_evidence(self):
        with self.assertRaises(AIFailure):
            self.turn('Tell me about a game', [
                reply({'parts': [{'text': 'An invented fact.', 'evidence': ['fake']}]})])
        self.assertEqual(self.model.exchange.call_count, 1)
        self.assertFalse(self.repo.mock_calls)

    def test_competing_preferences_fail_without_overwriting_saved_filters(self):
        self.turn('Keep a normal maximum of 30 USD.', [reply({
            'parts': [{'text': 'Noted.'}], 'preferences': {'set': [{'field': 'max_price_cents', 'value': 3000}]}})])
        conflicting = {'parts': [{'text': 'Restored.'}], 'preferences': {
            'set': [{'field': 'max_price_cents', 'value': 3000}], 'clear': ['max_price_cents']}}
        with self.assertRaises(ValueError):
            self.turn('Search with my normal requirements again.', [reply(conflicting)])
        self.assertEqual(self.model.exchange.call_count, 2)
        result = self.turn('Find games using my saved maximum.', [
            tools(('recommend_games', {'save_as_normal': False, 'query': '', 'filters': {}, 'finish': True})),
            answer('One is a catalog option.', [10], ['game:10:title'])])
        self.assertEqual(result['applied_filters']['max_price_cents'], 3000)
        self.assertEqual(len(result['games']), 1)
        self.assertEqual(self.model.exchange.call_count, 4)

    def test_previous_fact_card_cannot_bypass_new_recommendation_filters(self):
        self.turn('Show One and Two.', [tools(('lookup_titles', {'query': ''})),
            answer('One and Two are catalog titles.', [10, 20], ['game:10:title', 'game:20:title'])])
        # If the final writer chooses an older, unfiltered card, fail atomically
        # rather than displaying it. A large context may have already ended tool
        # use, so this check must not rely on an extra correction call.
        with self.assertRaises(AIFailure):
            self.turn('Now recommend only online co-op games.', [
                tools(('recommend_games', {'save_as_normal': False, 'query': 'cooperative games', 'filters': {'required_modes': ['online-co-op']}})),
                answer('Try One.', [10], ['game:10:title'])])
        self.assertEqual(self.archive.read(self.key)['document']['events'][-1]['status'], 'failed')
        self.assertEqual(self.repo.chat_candidates.call_count, 1)

    def test_hard_filter_correction_without_catalog_call_persists_and_missing_fields_retain_other_limits(self):
        self.model.exchange.side_effect = [answer('Noted.')]
        first = {'parts': [{'text': 'Noted.'}], 'preferences': {'set': [
            {'field': 'platforms', 'value': ['linux']}, {'field': 'max_price_cents', 'value': 3000},
            {'field': 'required_modes', 'value': ['online-co-op']}]}}
        self.turn('Online co-op on Linux, no higher than 30 USD.', [reply(first)])
        self.assertFalse(self.repo.mock_calls)
        correction = {'parts': [{'text': 'Windows replaces Linux; the other conditions stay.'}],
                      'preferences': {'set': [{'field': 'platforms', 'value': ['windows']}]}}
        self.turn('Correction: Windows instead, keep the other limits.', [reply(correction)])
        self.assertFalse(self.repo.mock_calls)
        self.turn('Recommend something with those conditions.', [
            tools(('recommend_games', {'save_as_normal': False, 'query': 'cooperative games', 'filters': {}})),
            answer('Two records online co-op.', [20], ['game:20:modes'])])
        filters = self.repo.chat_candidates.call_args.args[1]
        self.assertEqual(filters.platforms, ['windows'])
        self.assertEqual(filters.max_price_cents, 3000)
        self.assertEqual(filters.required_modes, ['online-co-op'])

    def test_turn_only_filter_change_does_not_overwrite_retained_requirements(self):
        self.turn('Keep a recorded budget of 1000 cents.', [reply({
            'parts': [{'text': 'Noted.'}], 'preferences': {'set': [{'field': 'max_price_cents', 'value': 1000}]}})])
        self.turn('For this search only, use 3000 cents.', [
            tools(('recommend_games', {'save_as_normal': False, 'query': 'games', 'filters': {'max_price_cents': 3000}})),
            answer('One is a catalog option.', [10], ['game:10:title'])])
        saved = self.archive.read(self.key)['document']['memory']['_catalog_requirements']['filters']
        self.assertEqual(saved['max_price_cents'], 1000)

    def test_temporary_budget_changes_retrieved_eligibility_then_restores_normal_search(self):
        cheap, expanded = game(10, 'Below normal ceiling'), game(20, 'Only inside expanded ceiling')
        cheap.price.amount_cents, expanded.price.amount_cents = 900, 2400
        self.repo = repository([cheap, expanded])
        normal = self.turn('Save a normal maximum of 10 USD and find options now.', [
            tools(('recommend_games', {'save_as_normal': True, 'query': 'games', 'filters': {'max_price_cents': 1000}, 'limit': 2})),
            answer('Here is a catalog option.', [10], ['game:10:title'])])
        temporary = self.turn('For this search only, use strictly above 10 USD through 30 USD.', [
            tools(('recommend_games', {'save_as_normal': False, 'query': 'games', 'filters': {'min_price_cents': 1001, 'max_price_cents': 3000}, 'limit': 2})),
            reply({'parts': [{'text': 'Here is a catalog option.', 'evidence': ['game:20:title']}],
                'game_ids': [20], 'preferences': {'scope': 'turn', 'set': [{'field': 'max_price_cents', 'value': 3000}]}})])
        restored = self.turn('Use my normal conditions again.', [
            tools(('recommend_games', {'save_as_normal': 'false', 'query': '', 'filters': {}})),
            tools(('recommend_games', {'save_as_normal': False, 'query': 'games', 'filters': {}, 'limit': 2, 'finish': True})),
            answer('Your normal maximum is $10 USD.', [10], [self.archive.read(self.key)['document']['events'][0]['id']])])
        self.assertEqual([c['game']['app_id'] for c in normal['games']], [10])
        self.assertEqual([c['game']['app_id'] for c in temporary['games']], [20])
        self.assertEqual([c['game']['app_id'] for c in restored['games']], [10])
        self.assertEqual(temporary['applied_filters']['max_price_cents'], 3000)
        self.assertEqual(temporary['applied_filters']['min_price_cents'], 1001)
        self.assertEqual(restored['applied_filters']['max_price_cents'], 1000)
        self.assertIsNone(restored['applied_filters']['min_price_cents'])
        self.assertIsNone(restored['preference_changes'])
        self.assertEqual(self.repo.chat_candidates.call_count, 3)
        self.assertIn('game:10:title', {source['id'] for source in restored['evidence']})
        self.assertEqual(self.archive.read(self.key)['document']['memory']['_catalog_requirements']['filters']['max_price_cents'], 1000)
        trace = self.archive.read(self.key)['document']['events'][-1]['attempts'][0]
        self.assertEqual(next(t['delivered']['error'] for t in trace if t.get('tool') == 'recommend_games'), 'invalid_tool_arguments')

    def test_four_recommendations_deliver_complete_essential_evidence_within_existing_bounds(self):
        originals = [game(100000 + i, f'Catalog adventure number {i}', ['single-player', 'online-co-op'],
                          description='An exploration and building adventure. ' * 12) for i in range(4)]
        self.repo = repository(originals)
        ids = [g.app_id for g in originals]
        result = self.turn('Suggest up to four Windows single-player games.', [
            tools(('recommend_games', {'save_as_normal': False, 'query': 'exploration', 'limit': 4,
                                      'filters': {'platforms': ['windows'], 'required_modes': ['single-player']}})),
            answer('Here are four recorded options.', ids, [f'game:{i}:title' for i in ids])])
        self.assertEqual([c['game']['app_id'] for c in result['games']], ids)
        trace = self.archive.read(self.key)['document']['events'][-1]['attempts'][0]
        delivery = next(t['delivered'] for t in trace if t.get('tool') == 'recommend_games')
        self.assertNotIn('error', delivery)
        self.assertEqual(delivery['returned'], 4)
        self.assertLessEqual(len(json.dumps(delivery, ensure_ascii=False, separators=(',', ':')).encode()), 6500)
        for original, packet in zip(originals, delivery['games'], strict=True):
            facts = {f['field']: f for f in packet['facts']}
            self.assertEqual(facts['price']['value'], original.price.model_dump(mode='json'))
            self.assertEqual(facts['platforms']['value'], original.platforms)
            self.assertEqual(facts['modes']['value'], original.modes)
            self.assertEqual(facts['free_to_play']['value'], original.free_to_play)
            description = facts['description']['value']
            self.assertLessEqual(len(description['excerpt']), 240)
            self.assertTrue(description['excerpt'].endswith('.'))
            self.assertEqual(description['excerpt'], original.description[:description['next_offset']])
            self.assertEqual(facts['genres']['value'], original.genres)
        packet = Dialogue(self.model, self.repo, self.archive, None).recommendation_packet(
            game(10, 'Long first sentence', description='Unbroken ' * 100 + '.'))
        description = next(f['value'] for f in packet['facts'] if f['field'] == 'description')
        self.assertEqual(description['excerpt'], '')
        self.assertEqual(description['next_offset'], 0)
        # The actual provider boundary is exercised, including full schema bytes.
        messages, active_tools, schema = self.model.exchange.call_args.args
        Dialogue.fit(copy.deepcopy(messages), active_tools, schema)

    def test_recommendation_defaults_to_ready_writer_without_redeciding_scope(self):
        description = 'Explore a ruined city.'
        self.repo = repository([game(10, 'One', description=description)])
        text = 'One could suit your interest in exploring a ruined city.'
        payload = json.loads(answer(text, [10], [f'game:10:description:0:{len(description)}'])['content'])
        payload['preferences'] = {'set': [{'field': 'max_price_cents', 'value': 3000}], 'scope': 'turn'}
        payload['memory'] = [{'key': 'friend', 'value': 'Alex'}]
        result = self.turn('My friend is Alex. Keep a normal maximum of 30 USD and show an exploration option.', [
            tools(('recommend_games', {'save_as_normal': True, 'query': 'exploration', 'filters': {'max_price_cents': 3000}})),
            {'content': json.dumps(payload)}])
        self.assertEqual(self.model.exchange.call_count, 2)
        final_messages, active_tools, schema = self.model.exchange.call_args_list[1].args
        self.assertEqual(active_tools, [])
        self.assertNotIn('preferences', schema['properties'])
        self.assertIn('memory', schema['properties'])
        self.assertTrue(any('No further tools' in (m.get('content') or '') for m in final_messages))
        for messages in (self.model.exchange.call_args_list[0].args[0], final_messages):
            self.assertIn('View details', messages[0]['content'])
            self.assertIn('THIS user', messages[0]['content'])
            self.assertIn("Current's game-discovery assistant", messages[0]['content'])
            self.assertIn('underlying provider, model, GPT version or architecture', messages[0]['content'])
            self.assertIn('non-game question first', messages[0]['content'])
            self.assertIn('Use Markdown when helpful', messages[0]['content'])
            self.assertNotIn('quote a short supplied sentence verbatim', messages[0]['content'])
        self.assertEqual(result['message'], text)
        self.assertEqual(result['games'][0]['game']['app_id'], 10)
        self.assertEqual(result['games'][0]['game']['description'], description)
        self.assertEqual(self.archive.read(self.key)['document']['memory']['_catalog_requirements']['filters']['max_price_cents'], 3000)
        self.assertEqual(self.archive.read(self.key)['document']['memory']['friend']['value'], 'Alex')

    def test_writer_projection_preserves_user_originals_but_omits_earlier_generated_prose(self):
        self.turn('Please keep this conversation available.', [answer('An unsupported earlier assistant claim about intergalactic penguin racing.')])
        original = copy.deepcopy(self.archive.read(self.key)['document']['events'][0])
        result = self.turn('Inspect One and its recorded mode.', [
            tools(('game_details', {'ids': [10], 'fields': ['modes', 'platforms'], 'finish': True})),
            answer('One records single-player.', [10], ['game:10:modes'])])
        self.assertEqual(result['games'][0]['game']['app_id'], 10)
        for call in self.model.exchange.call_args_list[-1:]:
            context = json.dumps(call.args[0])
            self.assertNotIn('intergalactic penguin', context)
            self.assertIn('Please keep this conversation available.', context)
            self.assertIn('game:10:modes', context)
            self.assertIn('recorded_support', context)
            self.assertIn('current compatibility unknown', context)
            self.assertEqual([m['content'] for m in call.args[0] if m['role'] == 'user'], ['Inspect One and its recorded mode.'])
        self.assertEqual(self.archive.read(self.key)['document']['events'][0], original)

    def test_valid_final_selection_is_not_rewritten_by_another_model_call(self):
        result = self.turn('Inspect both games, then show One.', [
            tools(('game_details', {'ids': [10, 20], 'fields': ['modes'], 'finish': False})),
            answer('One records single-player.', [10], ['game:10:modes']),
            answer('Two records online co-op.', [20], ['game:20:modes'])])
        self.assertEqual(self.model.exchange.call_count, 2)
        self.assertEqual([c['game']['app_id'] for c in result['games']], [10])

    def test_ready_flag_does_not_disable_a_planned_second_information_round(self):
        result = self.turn('Find the games, then compare the recorded modes.', [
            tools(('lookup_titles', {'query': '', 'finish': True})),
            tools(('game_details', {'ids': [10, 20], 'fields': ['modes'], 'finish': True})),
            answer('One records single-player; Two records online co-op.', [10, 20], ['game:10:modes', 'game:20:modes'])])
        self.assertEqual(len(result['games']), 2)
        self.assertTrue(self.model.exchange.call_args_list[1].args[1])
        trace = self.archive.read(self.key)['document']['events'][-1]['attempts'][0]
        self.assertFalse(next(t['delivered']['recommendation_search_performed'] for t in trace if t.get('tool') == 'lookup_titles'))
        self.assertEqual(self.model.exchange.call_count, 3)
        self.assertTrue(self.model.exchange.call_args_list[1].args[1])
        before = self.model.exchange.call_count
        result = self.turn('Recommend an option, then read its description before answering.', [
            tools(('recommend_games', {'save_as_normal': False, 'query': 'games', 'filters': {}, 'limit': 1, 'finish': False})),
            tools(('game_details', {'ids': [10], 'fields': ['description'], 'finish': True})),
            answer('One is a catalog option.', [10], ['game:10:title'])])
        self.assertEqual(self.model.exchange.call_count - before, 3)
        self.assertTrue(self.model.exchange.call_args_list[-2].args[1])
        self.assertEqual([c['game']['app_id'] for c in result['games']], [10])

    def test_refused_ready_page_keeps_tools_for_a_smaller_read_and_then_finalizes(self):
        self.repo = repository([game(100000 + i, f'Option {i}', description='Description ' * 1000)
                                for i in range(8)])
        result = self.turn('Inspect these records.', [
            tools(('game_details', {'ids': [100000 + i for i in range(8)], 'description_limit': 2000, 'finish': True})),
            tools(('game_details', {'ids': [100000], 'fields': ['title'], 'finish': True})),
            answer('Option 0 is in the catalog.', [100000], ['game:100000:title'])])
        self.assertEqual(len(result['games']), 1)
        self.assertEqual(self.model.exchange.call_count, 3)
        self.assertTrue(self.model.exchange.call_args_list[1].args[1])
        trace = self.archive.read(self.key)['document']['events'][-1]['attempts'][0]
        self.assertEqual(next(t['delivered']['error'] for t in trace if t.get('tool') == 'game_details'), 'tool_page_too_large')

    def test_direct_final_writer_still_rejects_invented_price_without_committing_preferences(self):
        payload = json.loads(answer('One has a recorded price of $9876.54 USD.', [10], ['game:10:price'])['content'])
        payload['preferences'] = {'set': [{'field': 'max_price_cents', 'value': 3000}]}
        with self.assertRaises(AIFailure):
            self.turn('Keep a normal maximum and show a recorded option.', [
                tools(('recommend_games', {'save_as_normal': True, 'query': '', 'filters': {'max_price_cents': 3000}, 'finish': True})),
                {'content': json.dumps(payload)}])
        self.assertEqual(self.model.exchange.call_count, 2)
        self.assertEqual(self.archive.read(self.key)['document']['memory'], {})
        with self.assertRaises(AIFailure):
            self.turn('Find an option again.', [
                tools(('recommend_games', {'save_as_normal': False, 'query': '', 'filters': {}, 'finish': True})),
                answer('No games found.')])
        self.assertEqual(self.model.exchange.call_count, 4)
        self.assertEqual(self.model.exchange.call_args.args[2]['properties']['game_ids']['minItems'], 1)

    def test_four_record_summaries_fit_after_retained_filters_and_long_native_call_ids(self):
        from datetime import datetime
        originals = [game(i, title, ['single-player', 'multiplayer', 'online-co-op', 'local-co-op'],
                          description='Explore, build and discover. ' * 15)
                     for i, title in ((400, 'Portal'), (105600, 'Terraria'), (620, 'Portal 2'),
                                      (311690, 'Enter the Gungeon'))]
        for original in originals:
            original.observed_at = datetime.fromisoformat('2026-10-14T18:52:53.328346+00:00')
            original.price.observed_at = original.observed_at
        self.repo = repository(originals)
        self.turn('Keep Windows and single-player, with an inclusive recorded maximum of 24 USD.', [
            reply({'parts': [{'text': 'Those are your usual requirements.'}], 'preferences': {'set': [
                {'field': 'platforms', 'value': ['windows']}, {'field': 'required_modes', 'value': ['single-player']},
                {'field': 'max_price_cents', 'value': 2400}]}})])
        request = tools(('recommend_games', {'save_as_normal': False, 'query': '', 'filters': {}, 'limit': 4}))
        request['tool_calls'][0]['id'] = 'fc_' + str(uuid4())
        ids = [g.app_id for g in originals]
        result = self.turn('Show four games using my usual conditions.', [request,
            answer('Here are four catalog options.', ids, [f'game:{i}:title' for i in ids])])
        self.assertEqual(len(result['games']), 4)
        trace = self.archive.read(self.key)['document']['events'][-1]['attempts'][0]
        self.assertNotIn('error', next(t['delivered'] for t in trace if t.get('tool') == 'recommend_games'))

    def test_refused_detail_page_cannot_expose_undelivered_games_or_sources(self):
        self.repo = repository([game(100000 + i, 'Long catalog title ' * 6,
                                     description='Very long description ' * 100) for i in range(8)])
        result = self.turn('Inspect a large page.', [
            tools(('game_details', {'ids': [100000 + i for i in range(8)], 'description_limit': 2000})),
            answer('The result was too large to verify. We can request a smaller page.')])
        trace = self.archive.read(self.key)['document']['events'][-1]['attempts'][0]
        refused = next(t for t in trace if t.get('tool') == 'game_details')
        self.assertEqual(refused['delivered']['result_state'], 'unknown_not_empty')
        self.assertEqual(len(refused['result']['games']), 8)
        self.assertEqual(result['games'], [])
        self.assertEqual(result['entities'], [])
        provider_messages = self.model.exchange.call_args.args[0]
        self.assertNotIn('game:100000:', json.dumps(provider_messages))
        self.assertEqual(result['evidence'], [])
        with patch.object(Dialogue, 'recommendation_packet', return_value={'padding': 'x' * 7000}):
            refused = self.turn('Save a budget and show options.', [
                tools(('recommend_games', {'save_as_normal': True, 'query': '', 'filters': {'max_price_cents': 3000}, 'finish': True})),
                answer('I could not deliver a complete result page.')])
        self.assertIsNone(refused['applied_filters'])
        self.assertNotIn('_catalog_requirements', self.archive.read(self.key)['document']['memory'])

    def test_fresh_four_game_evidence_replaces_cached_citations_without_changing_archive(self):
        originals = [game(100000 + i, f'Catalog option {i}', ['single-player', 'multiplayer', 'online-co-op'],
                          description='A long description with more detail available. ' * 8) for i in range(8)]
        for i, original in enumerate(originals):
            original.price.amount_cents = 900 if i < 4 else 1900
        self.repo = repository(originals)
        first_ids = [g.app_id for g in originals[:4]]
        first_sources = [f'game:{i}:{field}' for i in first_ids for field in ('title', 'price')]
        self.turn('Show four games below 12 USD.', [
            tools(('recommend_games', {'save_as_normal': False, 'query': '', 'filters': {'max_price_cents': 1200}, 'limit': 4})),
            answer('These are catalog options.', first_ids, first_sources)])
        before = copy.deepcopy(self.archive.read(self.key)['document']['events'][0])
        later_ids = [g.app_id for g in originals[4:]]
        result = self.turn('Now show four between 12.01 and 24 USD.', [
            tools(('recommend_games', {'save_as_normal': False, 'query': '', 'filters': {'min_price_cents': 1201, 'max_price_cents': 2400}, 'limit': 4})),
            answer('Here are the other catalog options.', later_ids, [f'game:{i}:title' for i in later_ids])])
        self.assertEqual([c['game']['app_id'] for c in result['games']], later_ids)
        self.assertEqual(self.archive.read(self.key)['document']['events'][0], before)
        schema = self.model.exchange.call_args.args[2]
        allowed = schema['$defs']['Passage']['properties']['evidence']['items']['enum']
        self.assertFalse(set(first_sources) & set(allowed))
        trace = self.archive.read(self.key)['document']['events'][-1]['attempts'][0]
        self.assertNotIn('error', next(t['delivered'] for t in trace if t.get('tool') == 'recommend_games'))

    def test_price_display_is_exact_record_derived_and_does_not_change_canonical_or_paged_values(self):
        dialogue = Dialogue(self.model, self.repo, self.archive, None)
        for cents, display in ((0, '$0.00 USD'), (1399, '$13.99 USD'), (1000000, '$10000.00 USD')):
            original = game(10, 'One')
            original.price.amount_cents = cents
            before = original.model_dump(mode='json')
            source = dialogue.game_packet(original, ['price'])['facts'][0]
            self.assertEqual(source['display_amount'], display)
            self.assertEqual(source['value'], before['price'])
            self.assertEqual(original.model_dump(mode='json'), before)
            page = dialogue.game_packet(original, ['price'], value_limit=10)['facts'][0]
            self.assertNotIn('display_amount', page)
            self.assertIsNotNone(page['value']['next_offset'])
        unknown = game(10, 'Unknown price')
        unknown.price = None
        self.assertNotIn('display_amount', dialogue.game_packet(unknown, ['price'])['facts'][0])

    def test_platform_packet_identifies_record_scope_and_keeps_false_distinct_from_missing(self):
        dialogue = Dialogue(self.model, self.repo, self.archive, None)
        original = game(10, 'One')
        packet = dialogue.game_packet(original, ['platforms', 'invented_compatibility'])
        source = packet['facts'][0]
        self.assertEqual(source['value'], original.platforms)
        self.assertIn('not_live_or_independently_verified', source['scope'])
        self.assertEqual(packet['unavailable_direct_fields'], ['invented_compatibility'])

    def test_provisional_search_cannot_commit_filters_before_final_scope_confirmation(self):
        self.turn('Keep a normal recorded budget of 1000 cents.', [reply({
            'parts': [{'text': 'Noted.'}], 'preferences': {'set': [{'field': 'max_price_cents', 'value': 1000}]}})])
        final = json.loads(answer('One is a catalog option.', [10], ['game:10:title'])['content'])
        final['preferences'] = {'scope': 'turn', 'set': [{'field': 'max_price_cents', 'value': 3000}]}
        self.turn('Only for now, allow 3000 cents.', [
            tools(('recommend_games', {'save_as_normal': False, 'query': '', 'filters': {'max_price_cents': 3000}})),
            reply(final)])
        saved = self.archive.read(self.key)['document']['memory']['_catalog_requirements']['filters']
        self.assertEqual(saved['max_price_cents'], 1000)
        self.assertEqual(self.repo.chat_candidates.call_args.args[0], 'games')
        packet = self.archive.read(self.key)['document']['events'][-1]['attempts'][0][1]['result']
        self.assertEqual(packet['retained_filters']['max_price_cents'], 1000)
        self.assertEqual(packet['filter_scope'], 'this_search_only')

    def test_search_is_read_only_and_only_a_valid_final_preference_edit_commits(self):
        result = self.turn('Keep a budget.', [
            tools(('recommend_games', {'save_as_normal': False, 'query': 'games', 'filters': {'max_price_cents': 3000}})),
            answer('One is an option.', [10], ['game:10:title'])])
        self.assertIsNone(result['preference_changes'])
        self.assertEqual(self.archive.read(self.key)['document']['memory'], {})
        self.turn('Keep that recorded maximum.', [reply({
            'parts': [{'text': 'Noted.'}], 'preferences': {'set': [{'field': 'max_price_cents', 'value': 3000}]}})])
        self.assertEqual(self.archive.read(self.key)['document']['memory']['_catalog_requirements']['filters']['max_price_cents'], 3000)
        before = copy.deepcopy(self.archive.read(self.key)['document']['memory'])
        with self.assertRaises(AIFailure):
            self.turn('Change the budget.', [
                tools(('recommend_games', {'save_as_normal': False, 'query': 'games', 'filters': {'max_price_cents': 4000}})),
                answer('Invented game.', [999], ['game:10:title'])])
        self.assertEqual(self.archive.read(self.key)['document']['memory'], before)

    def test_zero_description_limit_is_allowed_for_other_fields_but_never_gives_stuck_description_cursor(self):
        dialogue = Dialogue(self.model, self.repo, self.archive, None)
        packet = dialogue.tool('game_details', {'ids': [10], 'fields': ['price'], 'description_limit': 0}, {}, 'd')
        self.assertEqual(packet['games'][0]['facts'][0]['field'], 'price')
        blocked = dialogue.tool('game_details', {'ids': [10], 'fields': ['description'], 'description_limit': 0}, {}, 'd')
        self.assertEqual(blocked['error'], 'invalid_tool_arguments')

    def test_clear_budget_is_grouped_and_does_not_clear_platforms(self):
        initial = {'parts': [{'text': 'Noted.'}], 'preferences': {'set': [
            {'field': 'min_price_cents', 'value': 1000}, {'field': 'max_price_cents', 'value': 3000},
            {'field': 'platforms', 'value': ['linux']}]}}
        self.turn('Keep these conditions.', [reply(initial)])
        self.turn('Forget the budget, keep Linux.', [reply({
            'parts': [{'text': 'The budget is cleared; Linux stays.'}], 'preferences': {'clear': ['max_price_cents']}})])
        saved = self.archive.read(self.key)['document']['memory']['_catalog_requirements']['filters']
        self.assertEqual(saved['platforms'], ['linux'])
        self.assertNotIn('min_price_cents', saved)
        self.assertNotIn('max_price_cents', saved)


class DialogueApiTests(unittest.TestCase):
    def test_missing_archive_reports_configuration_not_a_new_chat_loop(self):
        from game_discovery.api.main import create_app
        key = {'conversation_id': str(uuid4()), 'token': 'a' * 43}
        with TestClient(create_app(Settings())) as client:
            for path, body in [('conversations', {'messages': []}), ('history', key), ('forget', key)]:
                response = client.post('/api/v2/assistant/' + path, json=body)
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.json()['code'], 'chat_service_configuration')
                self.assertNotEqual(response.json()['recovery'], 'new_chat')

    def test_capabilities_idempotency_history_and_erasure_across_new_app_instances(self):
        from game_discovery.api.main import create_app
        archive, model = MemoryArchive(), MagicMock()
        repo = repository()
        model.exchange.return_value = answer('Hello!')
        with TestClient(create_app(Settings(), conversation_store=archive, dialogue_model=model, repository=repo)) as client:
            created = client.post('/api/v2/assistant/conversations', json={'messages': []})
            self.assertEqual(created.status_code, 200)
            key = {k: created.json()[k] for k in ('conversation_id', 'token')}
            body = {**key, 'turn_id': str(uuid4()), 'revision': 0, 'message': 'Hi'}
            first = client.post('/api/v2/assistant', json=body)
            self.assertEqual(first.status_code, 200)
            repeat = client.post('/api/v2/assistant', json=body)
            self.assertEqual(repeat.json()['message'], 'Hello!')
            self.assertEqual(model.exchange.call_count, 1)
            rejected = client.post('/api/v2/assistant', json={**key, 'turn_id': str(uuid4()), 'revision': 1,
                                                           'message': 'Correction: I use Linux.'})
            self.assertEqual(rejected.status_code, 429)
            self.assertEqual(archive.read(ConversationKey(**key))['document']['events'][-1]['input'], 'Correction: I use Linux.')
        with TestClient(create_app(Settings(), conversation_store=archive, dialogue_model=model, repository=repo)) as restarted:
            history = restarted.post('/api/v2/assistant/history', json=key)
            self.assertEqual(history.json()['total'], 2)
            wrong = restarted.post('/api/v2/assistant/history', json={**key, 'token': 'z' * 43})
            self.assertEqual(wrong.status_code, 404)
            self.assertTrue(restarted.post('/api/v2/assistant/forget', json=key).json())
            self.assertEqual(restarted.post('/api/v2/assistant/history', json=key).status_code, 404)


if __name__ == '__main__':
    unittest.main()
