import type { Page } from '@playwright/test';
import type { DiscoverRequest, DiscoverResponse, Game } from '../src/api/discovery';
import { defaultFilters } from '../src/guest-store';
import type { AssistantTurn, AssistantReply, ArchiveEvent, ImportedMessage } from '../src/api/assistant';

const timestamp = '2026-10-14T18:52:00Z';
export const game = (app_id: number, title: string, cents = 1499): Game => ({ app_id, title,
  description: `${title} has a source-backed description.`, store_url: `https://store.steampowered.com/app/${app_id}/`,
  artwork_url: `https://shared.akamai.steamstatic.com/test/${app_id}.jpg`, eligibility: 'eligible', eligibility_reason: 'released_game',
  early_access: false, platforms: { windows: true, mac: true, linux: true }, genres: ['action', 'indie'], tags: [], modes: ['single-player'],
  free_to_play: false, price: { amount_cents: cents, currency: 'USD', region: 'US', observed_at: timestamp, evidence_id: `${app_id}:price` },
  observed_at: timestamp, semantic_hash: 'a'.repeat(64), evidence: [
    { id: `${app_id}:description`, field: 'description', value: 'Recorded description', source: { url: `https://store.steampowered.com/api/appdetails?appids=${app_id}`, collected_at: timestamp, sha256: 'a'.repeat(64) } },
    { id: `${app_id}:price`, field: 'price_cents', value: cents, source: { url: `https://store.steampowered.com/api/appdetails?appids=${app_id}`, collected_at: timestamp, sha256: 'a'.repeat(64) } },
  ] });
export const catalog = [game(1145360, 'Hades', 2499), game(107100, 'Bastion'), game(237930, 'Transistor', 1999), game(620, 'Portal 2', 999), game(367520, 'Hollow Knight')];
export function discovery(body: DiscoverRequest = { limit: 10 }): DiscoverResponse {
  const filters = { ...defaultFilters(), ...body.preferences, ...body.filters };
  const excluded = [...body.favorite_ids ?? [], ...filters.excluded_ids, ...(body.feedback ?? []).filter((f) => f.kind !== 'interested').map((f) => f.app_id)];
  const results = catalog.filter((g) => !excluded.includes(g.app_id) && !filters.free_only
    && (filters.min_price_cents === null || g.price!.amount_cents >= filters.min_price_cents)
    && (filters.max_price_cents === null || g.price!.amount_cents <= filters.max_price_cents)
    && filters.required_modes.every((mode) => g.modes!.includes(mode))
    && (!filters.platforms.length || (filters.platform_match === 'all' ? filters.platforms.every((platform) => g.platforms[platform] === true) : filters.platforms.some((platform) => g.platforms[platform] === true)))
    && filters.required_genres.every((genre) => g.genres!.includes(genre)))
    .map((game) => ({ game, reasons: [{ text: 'Source-backed catalog description.', evidence_ids: [`${game.app_id}:description`] }], tradeoffs: ['Recorded prices may differ from Steam today.'] }));
  return { request_id: `fixture-${Date.now()}-${Math.random()}`, catalog_version: 'fixture-v1', ranking_version: 'seed-feedback-v1',
    effective_criteria: filters, results, degraded_reasons: ['AI assistance is disabled. Catalog-derived explanations remain active.'], suggested_refinements: [], timings_ms: { core: 1 },
    effective_query: body.query ?? '', assistant_message: 'Your active criteria were retained. Experience preferences remain uncertain.', prompt_version: 'interpret-claims-v1' };
}
export async function mockCatalog(page: Page) {
  const requests: DiscoverRequest[] = [];
  await page.route('https://**/*', (route) => route.request().resourceType() === 'image'
    ? route.fulfill({ contentType: 'image/svg+xml', body: '<svg xmlns="http://www.w3.org/2000/svg" width="460" height="215"><rect width="460" height="215" fill="#1b2137"/></svg>' }) : route.abort());
  await page.route('**/api/v1/**', async (route) => {
    const url = new URL(route.request().url());
    if (url.pathname.endsWith('/games/resolve')) {
      const ids = route.request().postDataJSON().app_ids as number[];
      return route.fulfill({ json: { catalog_version: 'fixture-v1', items: catalog.filter((game) => ids.includes(game.app_id)), unknown_ids: ids.filter((id) => !catalog.some((game) => game.app_id === id)) } });
    }
    if (url.pathname.endsWith('/games')) {
      const items = catalog.filter((game) => game.title.toLowerCase().includes((url.searchParams.get('q') ?? '').toLowerCase()));
      return route.fulfill({ json: { catalog_version: 'fixture-v1', items, total: items.length, offset: 0 } });
    }
    if (url.pathname.endsWith('/facets')) return route.fulfill({ json: { catalog_version: 'fixture-v1', genres: ['action', 'indie', 'rpg'], tags: [], modes: ['single-player'], platforms: ['windows', 'mac', 'linux'], max_price_cents: 2499 } });
    if (url.pathname.endsWith('/discover')) {
      const body = route.request().postDataJSON() as DiscoverRequest;
      requests.push(body);
      return route.fulfill({ json: discovery(body) });
    }
    return route.fulfill({ status: 404, json: { code: 'game_not_found' } });
  });
  await mockAssistant(page);
  return requests;
}

export async function mockAssistant(page: Page, reply?: (body: AssistantTurn, previous: ArchiveEvent[]) => Partial<AssistantReply>) {
  const requests: AssistantTurn[] = [];
  const conversations = new Map<string, { token: string; revision: number; events: ArchiveEvent[] }>();
  await page.route('**/api/v2/assistant{,/**}', async route => {
    const path = new URL(route.request().url()).pathname;
    const body = route.request().postDataJSON();
    if (path.endsWith('/conversations')) {
      const key = body.key;
      if (!conversations.has(key.conversation_id)) {
        const events: ArchiveEvent[] = [];
        for (const m of body.messages as ImportedMessage[]) {
          if (m.role === 'user' || !events.length || events.at(-1)!.output) events.push({ id: crypto.randomUUID(), input: m.role === 'user' ? m.content : '', status: 'imported' });
          if (m.role === 'assistant') events.at(-1)!.output = { request_id: 'imported', message: m.content,
            games: catalog.filter(g => m.game_ids.includes(g.app_id)).map(game => ({ game, reasons: [], tradeoffs: [] })), notices: [], revision: events.length, total_turns: events.length };
        }
        conversations.set(key.conversation_id, { token: key.token, revision: events.length, events });
      }
      return route.fulfill({ json: { ...key, revision: conversations.get(key.conversation_id)!.revision } });
    }
    const row = conversations.get(body.conversation_id);
    if (path.endsWith('/forget')) { conversations.delete(body.conversation_id); return route.fulfill({ json: true }); }
    if (!row || row.token !== body.token) return route.fulfill({ status: 404, json: { code: 'chat_session_missing' } });
    if (path.endsWith('/history')) {
      const end = Math.min(row.events.length, body.before ?? row.events.length);
      const offset = Math.max(0, end - (body.limit ?? 10));
      return route.fulfill({ json: { revision: row.revision, total: row.events.length, offset, next_offset: end < row.events.length ? end : null, events: row.events.slice(offset, end) } });
    }
    requests.push(body);
    const response: AssistantReply = { request_id: 'assistant-fixture', message: 'Here are some catalog options.',
      games: discovery().results.slice(0, 2), notices: ['Recorded USD, not live prices.'], revision: row.revision + 1,
      total_turns: row.events.length + 1, ...reply?.(body, row.events) };
    row.revision = response.revision;
    row.events.push({ id: body.turn_id, input: body.message, status: 'done', output: response });
    return route.fulfill({ json: response });
  });
  return { requests, conversations };
}
