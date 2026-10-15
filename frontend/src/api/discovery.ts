import type { components } from './schema';
import { apiOrigin, ServiceError } from './client';

export type Game = components['schemas']['Game'];
export type Filters = Required<components['schemas']['Filters']>;
export type DiscoverRequest = components['schemas']['DiscoverRequest'];
export type DiscoverResponse = components['schemas']['DiscoverResponse'];
export type Facets = components['schemas']['Facets'];
export type GamePage = components['schemas']['GamePage'];

function record(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === 'object' && !Array.isArray(value);
}
function date(value: unknown): boolean { return typeof value === 'string' && !Number.isNaN(Date.parse(value)); }
function strings(value: unknown): value is string[] { return Array.isArray(value) && value.every((item) => typeof item === 'string'); }
function secureUrl(value: unknown): boolean {
  if (typeof value !== 'string') return false;
  try { const url = new URL(value); return url.protocol === 'https:' && !url.username && !url.password; } catch { return false; }
}
function isGame(value: unknown): value is Game {
  if (!record(value) || !record(value.platforms)) return false;
  return Number.isInteger(value.app_id) && Number(value.app_id) > 0 && typeof value.title === 'string'
    && typeof value.description === 'string' && secureUrl(value.store_url)
    && (value.artwork_url === null || secureUrl(value.artwork_url))
    && ['eligible', 'excluded', 'quarantined'].includes(String(value.eligibility))
    && (value.early_access === null || typeof value.early_access === 'boolean')
    && ['windows', 'mac', 'linux'].every((key) => value.platforms && record(value.platforms) && (value.platforms[key] === null || typeof value.platforms[key] === 'boolean'))
    && strings(value.genres) && strings(value.tags) && strings(value.modes) && date(value.observed_at)
    && (value.price === null || (record(value.price) && Number.isInteger(value.price.amount_cents) && Number(value.price.amount_cents) >= 0
      && value.price.currency === 'USD' && value.price.region === 'US' && date(value.price.observed_at) && typeof value.price.evidence_id === 'string'))
    && Array.isArray(value.evidence) && value.evidence.every((item) => record(item) && typeof item.id === 'string' && typeof item.field === 'string'
      && record(item.source) && secureUrl(item.source.url) && date(item.source.collected_at));
}
function isPage(value: unknown): value is GamePage {
  return record(value) && typeof value.catalog_version === 'string' && Array.isArray(value.items) && value.items.every(isGame)
    && Number.isInteger(value.total) && Number(value.total) >= 0 && Number.isInteger(value.offset);
}
function isFacets(value: unknown): value is Facets {
  return record(value) && typeof value.catalog_version === 'string' && strings(value.genres) && strings(value.tags) && strings(value.modes) && strings(value.platforms);
}
function isDiscovery(value: unknown): value is DiscoverResponse {
  return record(value) && typeof value.request_id === 'string' && typeof value.catalog_version === 'string'
    && value.ranking_version === 'seed-v1' && record(value.effective_criteria)
    && strings(value.suggested_refinements) && strings(value.degraded_reasons) && record(value.timings_ms)
    && Array.isArray(value.results) && value.results.every((item) => {
      if (!record(item) || !isGame(item.game)) return false;
      const game = item.game;
      return strings(item.tradeoffs) && Array.isArray(item.reasons) && item.reasons.every((reason) => record(reason)
        && typeof reason.text === 'string' && strings(reason.evidence_ids)
        && reason.evidence_ids.every((id) => game.evidence.some((e) => e.id === id)));
    });
}

async function request<T>(path: string, validate: (value: unknown) => value is T, signal: AbortSignal, body?: unknown): Promise<T> {
  const timeout = AbortSignal.timeout(75_000);
  let response: Response;
  try {
    response = await fetch(`${apiOrigin()}${path}`, { signal: AbortSignal.any([signal, timeout]), credentials: 'omit',
      method: body === undefined ? 'GET' : 'POST', headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body) });
  } catch (error) {
    if (signal.aborted || error instanceof ServiceError) throw error;
    throw new ServiceError(timeout.aborted ? 'The service took too long. Please try again.' : 'We couldn’t reach the catalog. The free service may be waking up; please try again.');
  }
  let value: unknown;
  try { value = await response.json(); } catch { throw new ServiceError('The service returned an unexpected response. Please try again.'); }
  if (!response.ok) {
    const code = record(value) ? value.code : '';
    throw new ServiceError(code === 'catalog_not_initialized' ? 'The catalog has not been published yet.'
      : code === 'unknown_favorite' ? 'A favorite is no longer in this catalog. Remove it and search again.'
      : code === 'game_not_found' ? 'This game is not in the current catalog.'
      : 'The catalog is temporarily unavailable. Please try again.', record(value) && typeof value.request_id === 'string' ? value.request_id : undefined);
  }
  if (!validate(value)) throw new ServiceError('The catalog response could not be verified. Please try again.');
  return value;
}

export const searchGames = (q: string, signal: AbortSignal) => request(`/api/v1/games?q=${encodeURIComponent(q)}&limit=12`, isPage, signal);
export const getFacets = (signal: AbortSignal) => request('/api/v1/facets', isFacets, signal);
export const getGame = (id: number, signal: AbortSignal) => request(`/api/v1/games/${id}`, isGame, signal);
export const discoverGames = (body: DiscoverRequest, signal: AbortSignal) => request('/api/v1/discover', isDiscovery, signal, body);
