import { spawn, spawnSync, type ChildProcess } from 'node:child_process';
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import type { DiscoverRequest, DiscoverResponse, Game } from '../src/api/discovery';
import { defaultFilters } from '../src/guest-store';

const root = path.resolve(import.meta.dirname, '../..');
const api = process.env.M3_API_ORIGIN || 'http://127.0.0.1:8001';
if (!['http://127.0.0.1:8001', 'http://127.0.0.1:8002'].includes(api)) throw new Error('The live check only permits its dedicated loopback API ports.');
const frontend = 'http://127.0.0.1:4173';
const captures = process.env.M3_CAPTURE_DIR || path.join(root, '.impeccable/review/m3');
let server: ChildProcess | undefined;
let startupError = false;
test.beforeAll(async () => {
  if (process.env.CI) throw new Error('The live M3 check is developer-only.');
  if (!process.env.API_PYTHON) throw new Error('Set API_PYTHON to the local locked backend environment interpreter.');
  let occupied = false;
  try { occupied = (await fetch(`${api}/health/live`)).ok; } catch { /* Require a free local API port. */ }
  if (occupied) throw new Error('The selected local API port is already occupied; stop that server before the explicit live check.');
  server = spawn(process.env.API_PYTHON, ['-m', 'uvicorn', 'game_discovery.api.main:app', '--host', '127.0.0.1', '--port', new URL(api).port, '--workers', '1'],
    { cwd: root, env: { ...process.env, ALLOWED_ORIGINS: frontend }, stdio: 'ignore', windowsHide: true });
  server.on('error', () => { startupError = true; });
  for (let i = 0; i < 100; i++) {
    if (startupError || server.exitCode !== null) throw new Error('The owned local API could not start. Check API_PYTHON and the local environment.');
    try { if ((await fetch(`${api}/health/live`)).ok) return; } catch { /* Bounded startup wait. */ }
    await new Promise((resolve) => setTimeout(resolve, 200));
  }
  throw new Error('The owned local API did not become live.');
});
test.afterAll(() => {
  if (!server?.pid) return;
  if (process.platform === 'win32') spawnSync('taskkill', ['/PID', String(server.pid), '/T', '/F'], { stdio: 'ignore' });
  else server.kill('SIGTERM');
});

test('real browser/API/database guest journey and controlled personalization', async ({ browser, request }) => {
  await mkdir(captures, { recursive: true });
  const cases: Record<string, number[]> = {};
  const body: DiscoverRequest = { favorite_ids: [1145360], filters: defaultFilters(), limit: 20 };
  const discover = async (name: string, input: DiscoverRequest) => {
    const response = await request.post(`${api}/api/v1/discover`, { data: input });
    expect(response.status()).toBe(200);
    const value = await response.json() as DiscoverResponse;
    expect(value.ranking_version).toBe('seed-feedback-v1');
    const expected = { ...defaultFilters(), ...input.preferences, ...input.filters };
    expect(value.effective_criteria).toMatchObject(expected);
    for (const { game } of value.results) {
      expect(game.app_id).not.toBe(1145360);
      if (expected.min_price_cents !== null) expect(game.price!.amount_cents).toBeGreaterThanOrEqual(expected.min_price_cents);
      if (expected.max_price_cents !== null) expect(game.price!.amount_cents).toBeLessThanOrEqual(expected.max_price_cents);
      if (expected.free_only) expect(game.free_to_play).toBe(true);
      if (expected.platforms.length) expect(expected.platform_match === 'all' ? expected.platforms.every((platform) => game.platforms[platform] === true) : expected.platforms.some((platform) => game.platforms[platform] === true)).toBe(true);
      expect(expected.required_modes.every((mode) => game.modes?.includes(mode))).toBe(true);
      expect(expected.required_genres.every((genre) => game.genres?.includes(genre))).toBe(true);
    }
    cases[name] = value.results.map((item) => item.game.app_id);
    return value;
  };
  const baseline = await discover('baseline', body);
  const feedback = (app_id: number, kind: 'interested' | 'not-for-me' | 'already-played') => ({ app_id, kind, timestamp: '2026-10-18T18:00:00Z' });
  const interested = await discover('interested', { ...body, feedback: [feedback(620, 'interested')] });
  expect(cases.interested).not.toEqual(cases.baseline);
  const played = await discover('already_played', { ...body, feedback: [feedback(107100, 'already-played')] });
  expect(cases.already_played).not.toContain(107100);
  const commonPlayed = new Set(played.results.map((item) => item.game.app_id));
  expect(baseline.results.filter((item) => commonPlayed.has(item.game.app_id)).map((item) => item.game.app_id))
    .toEqual(played.results.filter((item) => baseline.results.some((old) => old.game.app_id === item.game.app_id)).map((item) => item.game.app_id));
  await discover('not_for_me', { ...body, feedback: [feedback(107100, 'not-for-me')] });
  expect(cases.not_for_me).not.toContain(107100);
  expect(cases.not_for_me).not.toEqual(cases.already_played);
  const genre = await discover('required_rpg', { ...body, filters: { ...defaultFilters(), required_genres: ['rpg'] } });
  expect(genre.results.every((item) => item.game.genres?.includes('rpg'))).toBe(true);
  const override = await discover('explicit_overrides', { ...body, preferences: { ...defaultFilters(), max_price_cents: 1000, free_only: true }, filters: { ...defaultFilters(), free_only: false } });
  expect(override.effective_criteria).toMatchObject({ max_price_cents: 2000, free_only: false });
  const range = await discover('recorded_price_range', { ...body, filters: { ...defaultFilters(), min_price_cents: 1000, max_price_cents: 2000 } });
  expect(range.results.length).toBeGreaterThan(0);
  await discover('multiple_required_choices', { ...body, filters: { ...defaultFilters(), platforms: ['windows', 'mac'],
    required_modes: ['single-player', 'multiplayer'], required_genres: ['action', 'indie'] } });
  await discover('free_only_range', { ...body, filters: { ...defaultFilters(), min_price_cents: 0, max_price_cents: 0, free_only: true, required_modes: [] } });
  expect(interested.results.length).toBeGreaterThan(0);

  const scans: { device: string; state: string; overflow: boolean; axe: string[] }[] = [];
  const errors: string[] = [];
  for (const size of [{ name: 'desktop', width: 1440, height: 1000 }, { name: 'mobile', width: 390, height: 844 }]) {
    const context = await browser.newContext({ viewport: { width: size.width, height: size.height }, baseURL: frontend });
    const page = await context.newPage();
    page.on('pageerror', (error) => errors.push(error.message));
    const capture = async (state: string) => {
      await page.evaluate(() => document.fonts.ready);
      await page.locator('img').evaluateAll((images: HTMLImageElement[]) => Promise.all(images.map((image) => {
        image.loading = 'eager';
        return image.complete ? undefined : new Promise<void>((resolve) => {
          image.addEventListener('load', () => resolve(), { once: true });
          image.addEventListener('error', () => resolve(), { once: true });
          setTimeout(resolve, 10_000);
        });
      })));
      const axe = (await new AxeBuilder({ page }).analyze()).violations.map((item) => item.id);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
      expect(axe).toEqual([]); expect(overflow).toBe(false);
      scans.push({ device: size.name, state, overflow, axe });
      await page.screenshot({ path: path.join(captures, `${state}-${size.name}.png`), fullPage: true });
    };
    await page.goto('/');
    await expect(page.getByRole('slider', { name: 'Maximum recorded price', exact: true })).toBeEnabled({ timeout: 15000 });
    await capture('initial');
    for (const [name, choices, state] of [
      ['Required play modes', ['Multiplayer'], 'play-modes'],
      ['Required platform', ['macOS'], 'platforms'],
      ['Required catalog genre', ['Action', 'Indie'], 'genres'],
    ] as const) {
      const group = page.getByRole('group', { name, exact: true });
      await group.locator('summary').click();
      for (const choice of choices) await group.getByRole('checkbox', { name: choice, exact: true }).check();
      await capture(state);
      for (const choice of choices) await group.getByRole('checkbox', { name: choice, exact: true }).uncheck();
      await group.locator('summary').press('Escape');
    }
    await page.getByText('Change favorites', { exact: true }).click();
    await page.getByLabel('Search the catalog').fill('Hades');
    const searched = page.waitForResponse((response) => response.url().includes('/api/v1/games?q=Hades'), { timeout: 75000 });
    await page.getByRole('button', { name: 'Search', exact: true }).click();
    expect((await searched).status()).toBe(200);
    await expect(page.getByRole('button', { name: 'Hades Selected', exact: true })).toBeVisible({ timeout: 15000 });
    await capture('favorites');
    await page.getByText('Change favorites', { exact: true }).click();
    const answer = page.waitForResponse((response) => response.url() === `${api}/api/v1/discover`);
    await page.getByRole('button', { name: 'Find my next game', exact: true }).click();
    const response = await answer;
    expect(response.status()).toBe(200);
    expect(response.headers()['access-control-allow-origin']).toBe(frontend);
    const result = await response.json() as DiscoverResponse;
    expect(result.results.length).toBe(10);
    await expect(page.locator('.study-game')).toHaveCount(10);
    await capture('results');
    await page.locator('.study-game summary').first().click();
    await capture('evidence');
    const first: Game = result.results[0]!.game;
    await page.getByRole('button', { name: `Save ${first.title}`, exact: true }).click();
    await page.getByRole('group', { name: 'Recommendation feedback for Portal 2' }).getByRole('button', { name: 'Interested', exact: true }).click();
    const personalized = page.waitForResponse((reply) => reply.url() === `${api}/api/v1/discover`);
    await page.getByRole('button', { name: 'Find my next game', exact: true }).click();
    expect((await personalized).status()).toBe(200);
    await page.getByRole('link', { name: 'Saved games (1)' }).click();
    await page.reload();
    await expect(page.getByRole('heading', { name: first.title, exact: true })).toBeVisible();
    await expect(page.getByText('Portal 2 · Interested', { exact: true })).toBeVisible();
    await capture('saved');
    await page.getByText('Your device data', { exact: true }).click();
    await capture('device-data');
    await page.getByRole('button', { name: 'Clear my saved data', exact: true }).click();
    await expect(page.getByRole('link', { name: 'Saved games (0)' })).toBeVisible();
    await context.close();
  }
  expect(errors).toEqual([]);
  const report = { status: 'passed', observed_at: new Date().toISOString(), catalog_version: baseline.catalog_version,
    ranking_version: baseline.ranking_version, cases, scans, errors,
    note: 'Local API reads the existing restricted catalog. No migration, data import, deployment or relevance-quality claim.' };
  await writeFile(path.join(captures, 'report.json'), JSON.stringify(report, null, 2));
  if (process.env.M3_REPORT_PATH) await writeFile(process.env.M3_REPORT_PATH, `${JSON.stringify(report, null, 2)}\n`);
});
