import type { DiscoverResponse, Filters, Game } from './api/discovery';

export const GUEST_KEY = 'game-discovery:guest';
export const OWNED_PREFIX = 'game-discovery:';
export const LIMITS = { favorites: 50, saved: 200, feedback: 500, history: 20 } as const;
export type FeedbackKind = 'interested' | 'not-for-me' | 'already-played';
export type CachedGame = Pick<Game, 'app_id' | 'title' | 'store_url' | 'artwork_url'> & {
  price_cents: number | null;
  observed_at: string | null;
};
export type GuestFeedback = { app_id: number; title: string; kind: FeedbackKind; timestamp: string };
export type HistoryEntry = { id: string; timestamp: string; favorite_ids: number[]; preferences: Filters; result_ids: number[] };
export type GuestData = {
  version: 2;
  favorites: CachedGame[];
  preferences: Filters;
  saved: CachedGame[];
  feedback: GuestFeedback[];
  history: HistoryEntry[];
};
export type GuestSnapshot = { data: GuestData; epoch: number; persistent: boolean; notice: string };
type StoragePort = Pick<Storage, 'getItem' | 'setItem' | 'removeItem' | 'key' | 'length'>;

export const defaultFilters = (): Filters => ({ min_price_cents: 0, max_price_cents: 2000, price_operator: 'lte', free_only: false,
  platforms: ['windows'], platform_match: 'any', required_modes: ['single-player'], required_genres: [],
  preferred_terms: [], unwanted_terms: [], excluded_ids: [] });
const placeholder = (id: number): CachedGame => ({ app_id: id, title: id === 1145360 ? 'Hades' : `Game #${id}`,
  store_url: `https://store.steampowered.com/app/${id}/`, artwork_url: null, price_cents: null, observed_at: null });
const initial = (): GuestData => ({ version: 2, favorites: [placeholder(1145360)], preferences: defaultFilters(), saved: [], feedback: [], history: [] });
export const cacheGame = (game: Game): CachedGame => ({ app_id: game.app_id, title: game.title, store_url: game.store_url,
  artwork_url: game.artwork_url ?? null, price_cents: game.price?.amount_cents ?? null, observed_at: game.price?.observed_at ?? null });
const object = (value: unknown): value is Record<string, unknown> => !!value && typeof value === 'object' && !Array.isArray(value);
const id = (value: unknown): value is number => Number.isInteger(value) && Number(value) > 0 && Number(value) <= 2147483647;
const time = (value: unknown): value is string => typeof value === 'string' && value.length <= 40 && /(?:Z|[+-]\d{2}:\d{2})$/.test(value) && Number.isFinite(Date.parse(value));
const ids = (value: unknown, limit: number): value is number[] => Array.isArray(value) && value.length <= limit && value.every(id) && new Set(value).size === value.length;
const terms = (value: unknown): value is string[] => Array.isArray(value) && value.length <= 30 && value.every((term) => typeof term === 'string' && term.trim().length > 0 && term.length <= 100);
const oneOf = (value: unknown, values: readonly string[]) => typeof value === 'string' && values.includes(value);
const url = (value: unknown) => {
  if (typeof value !== 'string' || value.length > 2048) return false;
  try { const parsed = new URL(value); return parsed.protocol === 'https:' && !parsed.username && !parsed.password; } catch { return false; }
};
function filters(value: unknown): value is Filters {
  if (!object(value)) return false;
  const minimum = value.min_price_cents ?? null; // Existing v2 envelopes predate this optional field.
  return (value.max_price_cents === null || (Number.isInteger(value.max_price_cents) && Number(value.max_price_cents) >= 0 && Number(value.max_price_cents) <= 1000000))
    && (minimum === null || (Number.isInteger(minimum) && Number(minimum) >= 0 && Number(minimum) <= 1000000))
    && (minimum === null || value.max_price_cents === null || Number(minimum) <= Number(value.max_price_cents))
    && (!value.free_only || minimum === null || minimum === 0)
    && oneOf(value.price_operator, ['lte', 'lt']) && typeof value.free_only === 'boolean' && oneOf(value.platform_match, ['any', 'all'])
    && Array.isArray(value.platforms) && value.platforms.length <= 3 && value.platforms.every((v) => oneOf(v, ['windows', 'mac', 'linux']))
    && Array.isArray(value.required_modes) && value.required_modes.length <= 4 && value.required_modes.every((v) => oneOf(v, ['single-player', 'multiplayer', 'online-co-op', 'local-co-op']))
    && terms(value.required_genres) && terms(value.preferred_terms) && terms(value.unwanted_terms) && ids(value.excluded_ids, 200);
}
const cleanFilters = (value: Filters): Filters => ({ min_price_cents: value.min_price_cents ?? 0, max_price_cents: value.max_price_cents, price_operator: value.price_operator,
  free_only: value.free_only, platforms: [...new Set(value.platforms)], platform_match: value.platform_match,
  required_modes: [...new Set(value.required_modes)], required_genres: [...new Set(value.required_genres)],
  preferred_terms: [...new Set(value.preferred_terms)], unwanted_terms: [...new Set(value.unwanted_terms)], excluded_ids: [...value.excluded_ids] });
function cached(value: unknown): value is CachedGame {
  return object(value) && id(value.app_id) && typeof value.title === 'string' && value.title.length > 0 && value.title.length <= 300
    && url(value.store_url) && (value.artwork_url === null || url(value.artwork_url))
    && (value.price_cents === null || (Number.isInteger(value.price_cents) && Number(value.price_cents) >= 0))
    && (value.observed_at === null || time(value.observed_at));
}
function validFeedback(value: unknown): value is GuestFeedback {
  return object(value) && id(value.app_id) && typeof value.title === 'string' && value.title.length <= 300
    && oneOf(value.kind, ['interested', 'not-for-me', 'already-played']) && time(value.timestamp);
}
function history(value: unknown): value is HistoryEntry {
  return object(value) && typeof value.id === 'string' && value.id.length <= 100 && time(value.timestamp)
    && ids(value.favorite_ids, 50) && filters(value.preferences) && ids(value.result_ids, 20);
}
function list<T>(value: unknown, limit: number, validate: (value: unknown) => value is T): value is T[] {
  return Array.isArray(value) && value.length <= limit && value.every(validate);
}

/** A defined v1 format: ID-only favorites/saves and no history or required genre. */
export function decodeGuest(raw: string): GuestData {
  if (raw.length > 2_000_000) throw new Error('Storage too large');
  const value: unknown = JSON.parse(raw);
  if (!object(value)) throw new Error('Invalid guest storage');
  if (value.version === 1) {
    if (!ids(value.favorite_ids, 50) || !ids(value.saved_ids, 200) || !object(value.preferences)) throw new Error('Invalid v1 storage');
    const preferences = { ...defaultFilters(), ...value.preferences, required_genres: [] };
    const feedback = value.feedback ?? [];
    if (!filters(preferences) || !list(feedback, 500, validFeedback)) throw new Error('Invalid v1 preferences');
    const latest = new Map<number, GuestFeedback>();
    for (const item of feedback) {
      const previous = latest.get(item.app_id);
      if (!previous || Date.parse(item.timestamp) >= Date.parse(previous.timestamp)) latest.set(item.app_id, item);
    }
    // Run the migrated envelope through the same invariants as a native v2 one.
    return decodeGuest(JSON.stringify({ version: 2, favorites: value.favorite_ids.map(placeholder), saved: value.saved_ids.map(placeholder),
      preferences: cleanFilters(preferences), feedback: [...latest.values()], history: [] }));
  }
  if (value.version !== 2 || !list(value.favorites, 50, cached) || !list(value.saved, 200, cached)
    || !filters(value.preferences) || !list(value.feedback, 500, validFeedback) || !list(value.history, 20, history)
    || new Set(value.favorites.map((v) => v.app_id)).size !== value.favorites.length
    || new Set(value.saved.map((v) => v.app_id)).size !== value.saved.length
    || new Set(value.feedback.map((v) => v.app_id)).size !== value.feedback.length) throw new Error('Unsupported or invalid guest storage');
  // Return only allowlisted fields. Never pass arbitrary stored properties to the API.
  return { version: 2, favorites: value.favorites, preferences: cleanFilters(value.preferences), saved: value.saved, feedback: value.feedback,
    history: value.history.map((item) => ({ ...item, preferences: cleanFilters(item.preferences) })) };
}

export const rankingKey = (data: GuestData) => JSON.stringify([data.favorites.map((game) => game.app_id), data.preferences,
  data.feedback.map(({ app_id, kind, timestamp }) => ({ app_id, kind, timestamp }))]);

export function createGuestStore(local: StoragePort | null, session: StoragePort | null = null) {
  let snapshot: GuestSnapshot = { data: initial(), epoch: 0, persistent: !!local, notice: '' };
  let lastRaw: string | null = null;
  let protectedStorage = false;
  const listeners = new Set<() => void>();
  const emit = () => listeners.forEach((listener) => listener());
  const status = (notice: string, persistent = snapshot.persistent) => { snapshot = { ...snapshot, notice, persistent }; };
  function read(external = false) {
    if (!local) { status('Browser storage is unavailable. Changes last only until you leave or reload this page.', false); return false; }
    try {
      const raw = local.getItem(GUEST_KEY);
      if (raw === lastRaw && !protectedStorage) return true;
      lastRaw = raw;
      protectedStorage = false;
      try {
        const data = raw === null ? initial() : decodeGuest(raw);
        snapshot = { data, epoch: snapshot.epoch + (external && raw === null ? 1 : 0), persistent: true,
          notice: external ? (raw === null ? 'Saved data was cleared in another tab.' : 'Saved data updated in another tab. Your current shortlist was not resubmitted.') : '' };
      } catch {
        protectedStorage = true;
        status('We couldn’t open your saved preferences. The saved copy hasn’t been changed. Continue in this tab, or use Clear my saved data to start again.', false);
      }
      return !protectedStorage;
    } catch { status('Browser storage is blocked. Changes last only until you leave or reload this page.', false); return false; }
  }
  read();
  function persist() {
    if (!local || protectedStorage) return;
    try {
      const raw = JSON.stringify(snapshot.data);
      if (raw.length > 2_000_000) throw new Error('Storage bound exceeded');
      local.setItem(GUEST_KEY, raw);
      lastRaw = raw;
      snapshot = { ...snapshot, persistent: true, notice: '' };
    } catch { status('Your browser couldn’t save these changes. They’re available in this tab only. Check your browser’s storage settings before closing it, then choose Try saving again.', false); }
  }
  function update(action: (data: GuestData) => GuestData, ticket?: { epoch: number; key: string }) {
    const readable = !protectedStorage && read(true);
    if (ticket && (ticket.epoch !== snapshot.epoch || ticket.key !== rankingKey(snapshot.data))) { emit(); return false; }
    snapshot = { ...snapshot, data: action(snapshot.data) };
    if (readable) persist();
    emit();
    return true;
  }
  function limited(message: string) { status(message); emit(); return false; }
  const store = {
    getSnapshot: () => snapshot,
    subscribe: (listener: () => void) => { listeners.add(listener); return () => { listeners.delete(listener); }; },
    externalChange: (reset = false) => {
      let sessionFailed = false;
      if (reset) {
        // Session storage is tab-local: another tab's clear cannot remove this
        // tab's conversation directly, so erase owned session keys on the signal.
        try {
          const keys = session ? Array.from({ length: session.length }, (_, index) => session.key(index)) : [];
          for (const key of keys) if (key?.startsWith(OWNED_PREFIX)) session?.removeItem(key);
        } catch { sessionFailed = true; }
        snapshot = { data: initial(), epoch: snapshot.epoch + 1, persistent: !!local, notice: 'Saved data was cleared in another tab.' };
      }
      read(true);
      if (sessionFailed) status('Saved data was cleared in another tab, but this browser blocked removal of this tab’s conversation. Clear site data in browser settings to erase it.');
      emit();
    },
    ticket: () => { read(true); return { epoch: snapshot.epoch, key: rankingKey(snapshot.data) }; },
    current: (ticket: { epoch: number; key: string }) => { read(true); return ticket.epoch === snapshot.epoch && ticket.key === rankingKey(snapshot.data); },
    setPreferences(patch: Partial<Filters>) {
      read(true);
      const next = { ...snapshot.data.preferences, ...patch };
      const invalidPrice = next.min_price_cents != null && next.max_price_cents != null && next.min_price_cents > next.max_price_cents;
      if (!filters(next)) return limited(invalidPrice
        ? 'Choose a maximum price that’s at least your minimum price.' : 'Some filters need attention. Choose up to 30 genres and 200 excluded games, then try again.');
      return update((data) => ({ ...data, preferences: cleanFilters({ ...data.preferences, ...patch }) }));
    },
    toggleFavorite(game: CachedGame) {
      read(true);
      if (!snapshot.data.favorites.some((g) => g.app_id === game.app_id) && snapshot.data.favorites.length >= LIMITS.favorites) return limited('You can keep up to 50 favorites. Remove one before adding another.');
      return update((data) => ({ ...data, favorites: data.favorites.some((g) => g.app_id === game.app_id)
        ? data.favorites.filter((g) => g.app_id !== game.app_id) : [...data.favorites, game] }));
    },
    toggleSaved(game: CachedGame) {
      read(true);
      if (!snapshot.data.saved.some((g) => g.app_id === game.app_id) && snapshot.data.saved.length >= LIMITS.saved) return limited('You’ve saved 200 games. Open Saved games and remove one before saving another.');
      return update((data) => ({ ...data, saved: data.saved.some((g) => g.app_id === game.app_id)
        ? data.saved.filter((g) => g.app_id !== game.app_id) : [...data.saved, game] }));
    },
    setFeedback(game: CachedGame, kind: FeedbackKind | null) {
      read(true);
      if (kind && !snapshot.data.feedback.some((g) => g.app_id === game.app_id) && snapshot.data.feedback.length >= LIMITS.feedback) return limited('You can keep feedback on up to 500 games. Remove an older action before adding another.');
      return update((data) => ({ ...data, feedback: [...data.feedback.filter((item) => item.app_id !== game.app_id),
        ...(kind ? [{ app_id: game.app_id, title: game.title, kind, timestamp: new Date().toISOString() }] : [])] }));
    },
    addHistory(response: DiscoverResponse, ticket: { epoch: number; key: string }) {
      return update((data) => ({ ...data, history: [{ id: response.request_id, timestamp: new Date().toISOString(),
        favorite_ids: data.favorites.map((g) => g.app_id), preferences: filters(response.effective_criteria) ? cleanFilters(response.effective_criteria) : data.preferences, result_ids: response.results.map((r) => r.game.app_id) },
      ...data.history.filter((item) => item.id !== response.request_id)].slice(0, LIMITS.history) }), ticket);
    },
    removeHistory: () => update((data) => ({ ...data, history: [] })),
    retry: () => { if (read(true)) persist(); emit(); },
    clear() {
      let failed = !local;
      for (const storage of [local, session]) {
        if (!storage) continue;
        try {
          const keys = Array.from({ length: storage.length }, (_, index) => storage.key(index));
          for (const key of keys) if (key?.startsWith(OWNED_PREFIX)) storage.removeItem(key);
        } catch { failed = true; }
      }
      // Transient signal also invalidates requests in tabs which have not yet
      // persisted anything. No personal data or tombstone is left behind.
      if (local) {
        try { local.setItem(`${OWNED_PREFIX}reset`, String(Date.now())); local.removeItem(`${OWNED_PREFIX}reset`); }
        catch { failed = true; }
      }
      lastRaw = null;
      protectedStorage = failed;
      snapshot = { data: initial(), epoch: snapshot.epoch + 1, persistent: !!local && !failed,
        notice: failed ? 'This tab has been reset, but your browser blocked removal of stored data. Clear this site’s data in browser settings to remove the older copy.'
          : 'Saved data cleared. Initial Hades, Windows and $20 defaults restored.' };
      emit();
    },
  };
  return store;
}

export type GuestStore = ReturnType<typeof createGuestStore>;
export { filters as validFilters, cleanFilters as normalizeFilters };
