import type { components } from './schema';
import { apiOrigin, ServiceError } from './client';
import { parseServiceError, serviceError } from './errors';
import { validFilters } from '../guest-store';
import { decodeChatState, isChatState, type ChatState } from '../chat-state';
export { isChatState, type ChatState } from '../chat-state';

export type Game = components['schemas']['Game'];
export type Filters = Required<components['schemas']['Filters']>;
// Pydantic accepts omitted defaults and partial filters. The generated schema
// makes non-null defaults required, so expose the actual request-wire semantics.
export type DiscoverRequest = Omit<components['schemas']['DiscoverRequest'], 'query' | 'limit' | 'filters' | 'preferences' | 'conversation'> & {
  query?: string; limit?: number; filters?: Partial<Filters>; preferences?: Partial<Filters>;
  conversation?: { criteria?: Partial<Filters>; messages?: components['schemas']['ConversationMessage'][] };
};
export type DiscoverResponse = components['schemas']['DiscoverResponse'];
export type Facets = components['schemas']['Facets'];
export type GamePage = components['schemas']['GamePage'];
export type ResolvedGames = components['schemas']['ResolvedGames'];
export type ChatRequest = { message: string; messages: { role: 'user' | 'assistant'; content: string }[]; state: ChatState };
export type ChatResponse = Required<Omit<components['schemas']['ChatResponse'], 'state'>> & { state: ChatState };
export type Recommendation = DiscoverResponse['results'][number];

function record(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === 'object' && !Array.isArray(value);
}
function date(value: unknown): boolean { return typeof value === 'string' && !Number.isNaN(Date.parse(value)); }
function strings(value: unknown): value is string[] { return Array.isArray(value) && value.every((item) => typeof item === 'string'); }
function secureUrl(value: unknown): boolean {
  if (typeof value !== 'string') return false;
  try { const url = new URL(value); return url.protocol === 'https:' && !url.username && !url.password; } catch { return false; }
}
export function isGame(value: unknown): value is Game {
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
export function isRecommendation(value: unknown): value is Recommendation {
  if (!record(value) || !isGame(value.game)) return false;
  const game = value.game;
  return strings(value.tradeoffs) && Array.isArray(value.reasons) && value.reasons.every(reason => record(reason)
    && typeof reason.text === 'string' && strings(reason.evidence_ids)
    && reason.evidence_ids.every(id => game.evidence.some(entry => entry.id === id)));
}
export function isChatResponse(value: unknown): value is ChatResponse {
  return record(value) && typeof value.request_id === 'string' && typeof value.message === 'string' && !!value.message.trim() && value.message.length <= 2000
    && isChatState(value.state) && strings(value.notices) && Array.isArray(value.games) && value.games.length <= 4 && value.games.every(isRecommendation)
    && (value.catalog_version === null || typeof value.catalog_version === 'string');
}
function isPage(value: unknown): value is GamePage {
  return record(value) && typeof value.catalog_version === 'string' && Array.isArray(value.items) && value.items.every(isGame)
    && Number.isInteger(value.total) && Number(value.total) >= 0 && Number.isInteger(value.offset);
}
function isResolved(value: unknown): value is ResolvedGames {
  return record(value) && typeof value.catalog_version === 'string' && Array.isArray(value.items) && value.items.every(isGame)
    && Array.isArray(value.unknown_ids) && value.unknown_ids.every((id) => Number.isInteger(id) && id > 0);
}
function isFacets(value: unknown): value is Facets {
  return record(value) && typeof value.catalog_version === 'string' && strings(value.genres) && strings(value.tags) && strings(value.modes) && strings(value.platforms)
    && (value.max_price_cents === null || (Number.isInteger(value.max_price_cents) && Number(value.max_price_cents) >= 0));
}
function isDiscovery(value: unknown): value is DiscoverResponse {
  return record(value) && typeof value.request_id === 'string' && typeof value.catalog_version === 'string'
    && ['seed-v1', 'seed-feedback-v1', 'hybrid-text-v1'].includes(String(value.ranking_version)) && validFilters(value.effective_criteria)
    && (value.unresolved_preferences === undefined || strings(value.unresolved_preferences))
    && (value.effective_query === undefined || (typeof value.effective_query === 'string' && value.effective_query.length <= 2000))
    && (value.assistant_message === undefined || (typeof value.assistant_message === 'string' && value.assistant_message.length <= 2000))
    && (value.proposed_criteria === undefined || value.proposed_criteria === null || validFilters(value.proposed_criteria))
    && (value.conflicts === undefined || (Array.isArray(value.conflicts) && value.conflicts.length <= 10 && value.conflicts.every((item) => record(item)
      && typeof item.field === 'string' && typeof item.current === 'string' && typeof item.proposed === 'string')))
    && strings(value.suggested_refinements) && strings(value.degraded_reasons) && record(value.timings_ms)
    && Array.isArray(value.results) && value.results.every((item) => {
      if (!record(item) || !isGame(item.game)) return false;
      const game = item.game;
      return strings(item.tradeoffs) && Array.isArray(item.reasons) && item.reasons.every((reason) => record(reason)
        && typeof reason.text === 'string' && strings(reason.evidence_ids)
        && reason.evidence_ids.every((id) => game.evidence.some((e) => e.id === id)));
    });
}

export async function request<T>(path: string, validate: (value: unknown) => value is T, signal: AbortSignal, body?: unknown): Promise<T> {
  const chat = path === '/api/v1/chat' || path.startsWith('/api/v2/assistant');
  const timeout = AbortSignal.timeout(75_000);
  let response: Response;
  try {
    response = await fetch(`${apiOrigin()}${path}`, { signal: AbortSignal.any([signal, timeout]), credentials: 'omit',
      method: body === undefined ? 'GET' : 'POST', headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body) });
  } catch (error) {
    if (signal.aborted || error instanceof ServiceError) throw error;
    throw serviceError(timeout.aborted ? (chat ? 'chat_timeout' : 'request_timeout') : 'network_error');
  }
  let value: unknown;
  try { value = await response.json(); } catch (error) {
    if (signal.aborted) throw error;
    throw serviceError(timeout.aborted ? (chat ? 'chat_timeout' : 'request_timeout') : 'invalid_response');
  }
  if (!response.ok) {
    if (chat && response.status === 422 && (!record(value) || typeof value.code !== 'string')) throw serviceError('chat_incompatible');
    throw parseServiceError(value);
  }
  if (!validate(value)) throw serviceError('invalid_response');
  return value;
}

export const searchGames = (q: string, signal: AbortSignal) => request(`/api/v1/games?q=${encodeURIComponent(q)}&limit=12`, isPage, signal);
export const getFacets = (signal: AbortSignal) => request('/api/v1/facets', isFacets, signal);
export const getGame = (id: number, signal: AbortSignal) => request(`/api/v1/games/${id}`, isGame, signal);
export const resolveGames = (ids: number[], signal: AbortSignal) => request('/api/v1/games/resolve', isResolved, signal, { app_ids: ids });
export const discoverGames = (body: DiscoverRequest, signal: AbortSignal) => request('/api/v1/discover', isDiscovery, signal, body);
export const sendChat = async (body: ChatRequest, signal: AbortSignal): Promise<ChatResponse> => {
  const response = await request('/api/v1/chat', isChatResponse, signal, body);
  return { ...response, state: decodeChatState(response.state) };
};
