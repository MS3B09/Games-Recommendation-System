import { test, expect } from '@playwright/test';
import { cacheGame, createGuestStore, decodeGuest, defaultFilters, GUEST_KEY } from '../src/guest-store';
import { discovery, game } from './fixtures';

class MemoryStorage {
  values = new Map<string, string>();
  failWrite = false;
  get length() { return this.values.size; }
  key(index: number) { return [...this.values.keys()][index] ?? null; }
  getItem(key: string) { return this.values.get(key) ?? null; }
  setItem(key: string, value: string) { if (this.failWrite) throw new Error('Quota exceeded'); this.values.set(key, value); }
  removeItem(key: string) { this.values.delete(key); }
}

test('migrates the defined ID-only v1 envelope and forwards only allowlisted preferences', () => {
  const local = new MemoryStorage();
  local.setItem(GUEST_KEY, JSON.stringify({ version: 1, favorite_ids: [620], saved_ids: [107100], preferences: { ...defaultFilters(), injected: 'do not forward' }, feedback: [
    { app_id: 620, title: 'Portal 2', kind: 'interested', timestamp: '2026-10-18T10:00:00Z' },
    { app_id: 620, title: 'Portal 2', kind: 'not-for-me', timestamp: '2026-10-18T11:00:00Z' },
    { app_id: 620, title: 'Portal 2', kind: 'already-played', timestamp: '2026-10-18T11:00:00Z' },
  ] }));
  const store = createGuestStore(local);
  expect(store.getSnapshot().data.favorites[0]?.app_id).toBe(620);
  expect(store.getSnapshot().data.saved[0]?.app_id).toBe(107100);
  store.setPreferences({ platforms: [] });
  const written = JSON.parse(local.getItem(GUEST_KEY)!);
  expect(written.version).toBe(2);
  expect(written.preferences.platforms).toEqual([]);
  expect(written.preferences.injected).toBeUndefined();
  expect(decodeGuest(local.getItem(GUEST_KEY)!).feedback).toHaveLength(1);
  expect(createGuestStore(local).getSnapshot().data.feedback[0]?.kind).toBe('already-played');
});

test('retry rereads shared state before writing and respects another tab’s clear or future format', () => {
  const local = new MemoryStorage(); const first = createGuestStore(local);
  first.toggleSaved(cacheGame(game(620, 'Portal 2')));
  local.failWrite = true; first.setPreferences({ max_price_cents: 1000 });
  local.failWrite = false;
  const other = createGuestStore(local); other.toggleSaved(cacheGame(game(107100, 'Bastion')));
  // Do not deliver the storage event: retry itself must notice the newer data.
  first.retry();
  expect(decodeGuest(local.getItem(GUEST_KEY)!).saved.map((g) => g.app_id)).toEqual([620, 107100]);
  other.clear(); first.retry();
  expect(decodeGuest(local.getItem(GUEST_KEY)!).saved).toEqual([]);
  local.setItem(GUEST_KEY, '{"version":99}'); first.retry();
  expect(local.getItem(GUEST_KEY)).toBe('{"version":99}');
  expect(first.getSnapshot().persistent).toBe(false);
});

test('invalid, oversized and future data is protected; quota failures preserve this tab’s changes', () => {
  for (const raw of ['{bad', JSON.stringify({ version: 99 }), 'x'.repeat(2_000_001)]) {
    const local = new MemoryStorage(); local.setItem(GUEST_KEY, raw);
    const store = createGuestStore(local);
    store.toggleSaved(cacheGame(game(620, 'Portal 2')));
    expect(store.getSnapshot().data.saved).toHaveLength(1);
    expect(store.getSnapshot().persistent).toBe(false);
    expect(local.getItem(GUEST_KEY)).toBe(raw);
  }
  const local = new MemoryStorage(); const store = createGuestStore(local);
  local.failWrite = true;
  store.toggleSaved(cacheGame(game(620, 'Portal 2')));
  store.setPreferences({ max_price_cents: null });
  expect(store.getSnapshot().data.saved).toHaveLength(1);
  expect(store.getSnapshot().persistent).toBe(false);
  local.failWrite = false; store.retry();
  expect(decodeGuest(local.getItem(GUEST_KEY)!).saved).toHaveLength(1);
  expect(store.getSnapshot().persistent).toBe(true);
  const blocked = createGuestStore(null);
  blocked.clear();
  expect(blocked.getSnapshot().notice).toContain('blocked removal');
});

test('bounded saves, favorites, feedback and history never silently evict an explicit save', () => {
  const local = new MemoryStorage(); const store = createGuestStore(local);
  for (let id = 1; id <= 201; id++) store.toggleSaved(cacheGame(game(id, `Game ${id}`)));
  expect(store.getSnapshot().data.saved).toHaveLength(200);
  expect(store.getSnapshot().notice).toContain('200');
  expect(store.getSnapshot().data.saved[0]?.app_id).toBe(1);
  for (let id = 1; id <= 51; id++) store.toggleFavorite(cacheGame(game(id, `Game ${id}`)));
  expect(store.getSnapshot().data.favorites).toHaveLength(50);
  for (let id = 1; id <= 501; id++) store.setFeedback(cacheGame(game(id, `Game ${id}`)), 'interested');
  expect(store.getSnapshot().data.feedback).toHaveLength(500);
  store.setFeedback(cacheGame(game(1, 'Game 1')), 'already-played');
  expect(store.getSnapshot().data.feedback.filter((item) => item.app_id === 1)).toHaveLength(1);
  expect(store.getSnapshot().data.feedback.find((item) => item.app_id === 1)?.kind).toBe('already-played');
  for (let i = 0; i < 25; i++) store.addHistory({ ...discovery(), request_id: `request-${i}` }, store.ticket());
  expect(store.getSnapshot().data.history).toHaveLength(20);
  expect(store.getSnapshot().data.history[0]?.id).toBe('request-24');
});

test('clear removes only owned local/session data and rejects all pre-clear responses', () => {
  const local = new MemoryStorage(); const session = new MemoryStorage(); const store = createGuestStore(local, session);
  local.setItem('other-app', 'keep'); session.setItem('other-app', 'keep');
  session.setItem('game-discovery:conversation', 'old session');
  store.toggleSaved(cacheGame(game(620, 'Portal 2')));
  const pending = store.ticket();
  store.clear();
  expect(store.addHistory(discovery(), pending)).toBe(false);
  expect(store.getSnapshot().data.saved).toEqual([]);
  expect(local.getItem(GUEST_KEY)).toBeNull();
  expect(session.getItem('game-discovery:conversation')).toBeNull();
  expect(local.getItem('other-app')).toBe('keep');
  expect(session.getItem('other-app')).toBe('keep');
});

test('tab updates merge a new action onto current device state and stale history cannot resurrect it', () => {
  const local = new MemoryStorage(); const first = createGuestStore(local); const second = createGuestStore(local);
  const pending = second.ticket();
  first.toggleSaved(cacheGame(game(620, 'Portal 2')));
  second.setPreferences({ max_price_cents: 1000 });
  expect(decodeGuest(local.getItem(GUEST_KEY)!).saved[0]?.app_id).toBe(620);
  expect(second.addHistory(discovery(), pending)).toBe(false);
  first.clear(); second.externalChange(true);
  expect(second.getSnapshot().data.saved).toEqual([]);
  expect(second.getSnapshot().epoch).toBeGreaterThan(0);
});
