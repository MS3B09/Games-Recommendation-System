"""Freeze the approved 2,000-game expansion's bounded candidate queue, not eligibility."""

import csv
import hashlib
import json
import re
import time
from collections import defaultdict
from pathlib import Path

from game_discovery.jobs.audit import steam_app_id
from game_discovery.jobs.catalog import fetch_source, write_json

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / 'data/raw/catalog-expansion-2000-2026-11-05'


def prepare():
    if (OUTPUT / 'candidate-manifest.json').exists():
        raise ValueError('Existing immutable candidate manifest; reuse it instead of replacing it')
    OUTPUT.mkdir(parents=True, exist_ok=True)
    queue = {}

    def add(app_id, title, reason, origin, hints=None):
        if app_id in queue:
            return
        if type(app_id) is not int or not 0 < app_id <= 2147483647:
            raise ValueError('Invalid candidate identity')
        queue[app_id] = {'app_id': app_id, 'title_lead': title, 'reason': reason,
                         'origin': origin, 'coverage_hints_not_facts': hints or {}}

    active = json.loads((ROOT / 'data/reports/catalog-capacity-2026-11-05/active-games.json').read_text(encoding='utf-8'))
    required = json.loads((ROOT / 'data/fixtures/m2-app-ids.json').read_text(encoding='utf-8'))
    titles = {g['app_id']: g['title'] for g in active}
    for app_id in required:
        add(app_id, titles[app_id], 'retain existing eligible identity; refresh source', 'active_catalog')
    for group, leads in json.loads((ROOT / 'data/fixtures/catalog-expansion-curated.json').read_text(encoding='utf-8')).items():
        for app_id, title in leads:
            add(app_id, title, 'curated genre/budget/play-style gap lead; not validated popularity', 'curated', {'group': group})
    # This structured ranking supplies identity leads only; appdetails must still prove eligibility.
    url = 'https://api.steampowered.com/ISteamChartsService/GetMostPlayedGames/v1/'
    body, source = fetch_source(url)
    (OUTPUT / 'most-played-leads.json').write_bytes(body)
    charts = json.loads(body)['response']
    if not isinstance(charts.get('ranks'), list) or len(charts['ranks']) > 1000:
        raise ValueError('Invalid bounded chart leads')
    for row in charts['ranks']:
        add(row['appid'], None, 'Steam most-played snapshot lead; may include non-games', 'steam_charts',
            {'recorded_rank': row['rank'], 'recorded_peak_players': row.get('peak_in_game'), 'rollup_date': charts.get('rollup_date')})
    time.sleep(2)
    legacy = {}
    input_hashes = {}
    excluded_leads = 0
    avoid = re.compile(r'\b(dlc|soundtrack|demo|prologue|playtest|dedicated server|artbook|wallpaper|hentai|sex|porn|erotic|nude)\b', re.I)
    for filename in ('games_data_recomendation.csv', 'game_data_for_dashboard.csv'):
        path = ROOT / filename
        with path.open('rb') as stream:
            input_hashes[filename] = hashlib.file_digest(stream, 'sha256').hexdigest()
        with path.open(encoding='utf-8-sig', newline='') as stream:
            for row in csv.DictReader(stream):
                app_id = steam_app_id(row.get('Link', ''))
                if app_id is None or app_id in queue:
                    continue
                title = row.get('title', '').strip()
                if not title or avoid.search(title):
                    excluded_leads += 1
                    continue
                count = row.get('review_count', '').replace(',', '').strip()
                count = int(count) if count.isdigit() else 0
                genre = row.get('genre', '')
                previous = legacy.get(app_id)
                if previous is None or count > previous['legacy_review_count']:
                    legacy[app_id] = {'app_id': app_id, 'title': title, 'genre_raw': genre,
                                     'legacy_review_count': count, 'origin': filename}
    buckets = defaultdict(list)
    for row in legacy.values():
        group = next((g for g in ('strategy', 'simulation', 'rpg', 'casual', 'adventure', 'action')
                      if g in row['genre_raw'].casefold()), 'other')
        buckets[group].append(row)
    for rows in buckets.values():
        rows.sort(key=lambda r: (-r['legacy_review_count'], r['app_id']))
    offsets = defaultdict(int)
    while len(queue) < 2500:
        before = len(queue)
        for group in sorted(buckets):
            index = offsets[group]
            if index < len(buckets[group]) and len(queue) < 2500:
                row = buckets[group][index]
                offsets[group] += 1
                add(row['app_id'], row['title'], 'legacy lead selected in balanced genre-hint rotation; all facts need fresh validation',
                    row['origin'], {'legacy_genre_raw': row['genre_raw'], 'legacy_review_count': row['legacy_review_count']})
        if len(queue) == before:
            raise ValueError('Insufficient candidate leads')
    ids = list(queue)
    assert len(ids) == len(set(ids)) == 2500 and ids[:40] == required
    manifest = {'schema_version': 1, 'eligible_target': 2000, 'required_ids': required,
                'note': 'Candidate leads only. Title/genre/review hints are not activated facts or popularity judgments.',
                'chart_source': source.model_dump(mode='json'), 'legacy_input_sha256': input_hashes,
                'title_heuristic_excluded_leads_not_eligibility_decisions': excluded_leads,
                'candidates': list(queue.values())}
    write_json(OUTPUT / 'candidate-manifest.json', manifest)
    write_json(OUTPUT / 'candidate-ids.json', ids)
    write_json(OUTPUT / 'required-ids.json', required)
    print(json.dumps({'candidates': len(ids), 'required': len(required), 'target': 2000,
                      'origins': {origin: sum(r['origin'] == origin for r in queue.values())
                                  for origin in sorted({r['origin'] for r in queue.values()})}}))


if __name__ == '__main__':
    try:
        prepare()
    except Exception as error:
        print(json.dumps({'status': 'failed', 'error_type': type(error).__name__}))
        raise SystemExit(1)
