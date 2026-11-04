import type { components } from './api/schema';
import { validFilters } from './guest-store';

export type ChatCriteria = Required<components['schemas']['ChatCriteria']>;
export type ChatOrigin = Required<components['schemas']['Origin']>;
export type ChatState = Required<Omit<components['schemas']['ChatStateV2Wire'], 'criteria' | 'provenance' | 'query_origin' | 'exclusions' | 'legacy_criteria'>> & {
  criteria: ChatCriteria; provenance: Record<string, ChatOrigin>; query_origin: ChatOrigin | null;
  exclusions: { app_id: number; origin: ChatOrigin }[]; legacy_criteria: ChatCriteria | null;
};
export type LegacyChatState = Omit<Required<components['schemas']['ChatState']>, 'criteria'> & { criteria: ChatCriteria };
export const neutralChatCriteria = (): ChatCriteria => ({ min_price_cents: null, max_price_cents: null,
  price_operator: 'lte', free_only: false, platforms: [], platform_match: 'any', required_modes: [],
  required_genres: [], preferred_terms: [], unwanted_terms: [], excluded_ids: [] });
export const neutralChatState = (): ChatState => ({ version: 2, user_turn: 0, criteria: neutralChatCriteria(),
  provenance: {}, query: '', query_origin: null, exclusions: [], shown_ids: [], referenced_ids: [],
  legacy_criteria: null, legacy_query: '', legacy_excluded_ids: [] });
const object = (value: unknown): value is Record<string, unknown> => !!value && typeof value === 'object' && !Array.isArray(value);
const keys = (value: Record<string, unknown>, allowed: string[]) => Object.keys(value).every(key => allowed.includes(key));
const integer = (value: unknown, min: number, max: number): value is number => Number.isInteger(value) && Number(value) >= min && Number(value) <= max;
const text = (value: unknown): value is string => typeof value === 'string' && Array.from(value).length <= 1000;
const ids = (value: unknown, max: number): value is number[] => Array.isArray(value) && value.length <= max
  && value.every(id => integer(id, 1, 2147483647)) && new Set(value).size === value.length;
const criterionKeys = Object.keys(neutralChatCriteria());
const originKeys = criterionKeys.filter(key => key !== 'excluded_ids');

function criteria(value: unknown, legacy = false): ChatCriteria {
  if (!object(value) || !keys(value, criterionKeys)) throw new Error('Invalid chat criteria');
  const merged = { ...neutralChatCriteria(), ...value };
  if (!validFilters(merged) || (!legacy && merged.excluded_ids.length)) throw new Error('Invalid chat criteria');
  // Match catalog normalization, without the main page's zero-minimum default.
  return { ...merged, platforms: [...new Set(merged.platforms)], required_modes: [...new Set(merged.required_modes)],
    required_genres: [...new Set(merged.required_genres.map(term => term.trim().toLowerCase()))].sort(),
    preferred_terms: [...new Set(merged.preferred_terms.map(term => term.trim().toLowerCase()))].sort(),
    unwanted_terms: [...new Set(merged.unwanted_terms.map(term => term.trim().toLowerCase()))].sort() };
}
function origin(value: unknown, turn: number): ChatOrigin {
  if (!object(value) || !keys(value, ['user_turn', 'scope']) || !integer(value.user_turn, 1, turn)
    || (value.scope !== undefined && value.scope !== 'conversation')) throw new Error('Invalid chat provenance');
  return { user_turn: value.user_turn, scope: 'conversation' };
}
export function decodeChatState(value: unknown): ChatState {
  const neutral = neutralChatState();
  if (!object(value) || value.version !== 2 || !keys(value, Object.keys(neutral))) throw new Error('Unsupported chat state');
  const state = { ...neutral, ...value };
  if (!integer(state.user_turn, 0, 1000000) || !text(state.query) || !text(state.legacy_query)
    || !ids(state.shown_ids, 4) || !ids(state.referenced_ids, 2) || !ids(state.legacy_excluded_ids, 100)
    || !object(state.provenance) || !keys(state.provenance, originKeys) || !Array.isArray(state.exclusions)
    || state.exclusions.length > 100) throw new Error('Invalid chat state');
  const active = criteria(state.criteria);
  const provenance = Object.fromEntries(Object.entries(state.provenance).map(([key, value]) => [key, origin(value, state.user_turn)]));
  const defaults = neutralChatCriteria();
  if (originKeys.some(key => JSON.stringify(active[key as keyof ChatCriteria]) !== JSON.stringify(defaults[key as keyof ChatCriteria]) && !provenance[key])) {
    throw new Error('Chat requirements need provenance');
  }
  const queryOrigin = state.query_origin === null ? null : origin(state.query_origin, state.user_turn);
  if (!!state.query.trim() !== !!queryOrigin) throw new Error('Chat query needs provenance');
  const exclusions = state.exclusions.map(item => {
    if (!object(item) || !keys(item, ['app_id', 'origin']) || !integer(item.app_id, 1, 2147483647)) throw new Error('Invalid chat exclusion');
    return { app_id: item.app_id, origin: origin(item.origin, state.user_turn) };
  });
  if (new Set(exclusions.map(item => item.app_id)).size !== exclusions.length) throw new Error('Duplicate chat exclusions');
  return { version: 2, user_turn: state.user_turn, criteria: active, provenance, query: state.query,
    query_origin: queryOrigin, exclusions, shown_ids: [...state.shown_ids], referenced_ids: [...state.referenced_ids],
    legacy_criteria: state.legacy_criteria === null ? null : criteria(state.legacy_criteria),
    legacy_query: state.legacy_query, legacy_excluded_ids: [...state.legacy_excluded_ids] };
}
export function decodeLegacyChatState(value: unknown): LegacyChatState {
  if (!object(value) || !keys(value, ['criteria', 'query', 'excluded_ids', 'shown_ids']) || !text(value.query)
    || !ids(value.excluded_ids, 100) || !ids(value.shown_ids, 4) || !object(value.criteria)
    || !validFilters(value.criteria)) throw new Error('Invalid legacy chat state');
  return { criteria: criteria(value.criteria, true), query: value.query, excluded_ids: [...value.excluded_ids], shown_ids: [...value.shown_ids] };
}
export function migrateChatState(value: unknown): ChatState {
  const legacy = decodeLegacyChatState(value);
  const exclusions = [...new Set([...legacy.excluded_ids, ...legacy.criteria.excluded_ids])];
  if (exclusions.length > 100) throw new Error('Legacy chat exclusions exceed the new bound');
  return { ...neutralChatState(), shown_ids: legacy.shown_ids, legacy_query: legacy.query,
    legacy_criteria: { ...legacy.criteria, excluded_ids: [] }, legacy_excluded_ids: exclusions };
}
export function isChatState(value: unknown): value is ChatState {
  try { decodeChatState(value); return true; } catch { return false; }
}
