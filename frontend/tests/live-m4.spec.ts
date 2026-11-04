import { spawn, spawnSync, type ChildProcess } from 'node:child_process';
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import type { DiscoverRequest, DiscoverResponse, Filters } from '../src/api/discovery';
import { defaultFilters } from '../src/guest-store';

const root = path.resolve(import.meta.dirname, '../..');
const api = process.env.M4_API_ORIGIN || 'http://127.0.0.1:8002';
const frontend = 'http://127.0.0.1:4173';
const captures = process.env.M4_CAPTURE_DIR || path.join(root, '.impeccable/review/independent-assistant-live');
const acceptance = 'I loved Hades for its combat and sense of progression. I want another satisfying single-player game, but with less repetition, playable on Windows, under $20.';
let server: ChildProcess | undefined;
test.beforeAll(async () => {
  if (process.env.CI || !process.env.API_PYTHON || !['http://127.0.0.1:8001', 'http://127.0.0.1:8002'].includes(api)) throw new Error('Developer-only check: configure API_PYTHON and a dedicated allowed loopback port.');
  let occupied = false;
  try { occupied = (await fetch(`${api}/health/live`, { signal: AbortSignal.timeout(2000) })).ok; } catch { /* Only start on a free API port. */ }
  if (occupied) throw new Error('The selected API port is occupied. Choose another allowed port; the check will not stop an unrelated service.');
  server = spawn(process.env.API_PYTHON, ['-m', 'uvicorn', 'game_discovery.api.main:app', '--host', '127.0.0.1', '--port', new URL(api).port, '--workers', '1'],
    { cwd: root, env: { ...process.env, ALLOWED_ORIGINS: frontend, AI_ENABLED: 'false' }, stdio: 'ignore', windowsHide: true });
  let failed = false;
  server.on('error', () => { failed = true; });
  for (let attempt = 0; attempt < 150; attempt++) {
    if (failed || server.exitCode !== null) throw new Error('Owned M4 API could not start. Check the local backend environment.');
    try { if ((await fetch(`${api}/health/live`, { signal: AbortSignal.timeout(1000) })).ok) return; } catch { /* Bounded startup wait. */ }
    await new Promise((resolve) => setTimeout(resolve, 200));
  }
  throw new Error('Owned M4 API did not become live.');
});
test.afterAll(() => {
  if (!server?.pid) return;
  if (process.platform === 'win32') spawnSync('taskkill', ['/PID', String(server.pid), '/T', '/F'], { stdio: 'ignore' });
  else server.kill('SIGTERM');
});

test('real main discovery, single-row dismissal, independent unavailable chat and legacy API compatibility', async ({ browser, request }) => {
  await mkdir(captures, { recursive: true });
  const cases: { name: string; ids: number[]; titles: string[]; criteria: DiscoverResponse['effective_criteria']; core_ms: number; semantic: boolean }[] = [];
  const discover = async (name: string, body: DiscoverRequest) => {
    const reply = await request.post(`${api}/api/v1/discover`, { data: body, timeout: 75000 });
    expect(reply.status()).toBe(200);
    const value = await reply.json() as DiscoverResponse;
    const criteria = value.effective_criteria as Filters;
    for (const item of value.results) {
      expect(item.game.eligibility).toBe('eligible');
      expect(body.favorite_ids ?? []).not.toContain(item.game.app_id);
      if (criteria.max_price_cents !== null) {
        expect(item.game.price).not.toBeNull();
        if (criteria.price_operator === 'lt') expect(item.game.price!.amount_cents).toBeLessThan(criteria.max_price_cents);
        else expect(item.game.price!.amount_cents).toBeLessThanOrEqual(criteria.max_price_cents);
      }
      if (criteria.min_price_cents !== null) expect(item.game.price!.amount_cents).toBeGreaterThanOrEqual(criteria.min_price_cents);
      expect(criteria.platforms.every((platform) => item.game.platforms[platform] === true)).toBe(true);
      expect(criteria.required_modes.every((mode) => item.game.modes?.includes(mode))).toBe(true);
      for (const reason of item.reasons) {
        expect(reason.evidence_ids.length).toBeGreaterThan(0);
        expect(reason.evidence_ids.every((id) => item.game.evidence.some((evidence) => evidence.id === id))).toBe(true);
      }
    }
    cases.push({ name, ids: value.results.map((item) => item.game.app_id), titles: value.results.map((item) => item.game.title),
      criteria, core_ms: value.timings_ms.core!, semantic: !!value.capabilities?.semantic_query_matching });
    return value;
  };
  const hades = await discover('hades_acceptance', { query: acceptance, favorite_ids: [1145360], filters: defaultFilters(), limit: 10 });
  expect(hades.results.length).toBeGreaterThan(0);
  expect(hades.ranking_version).toBe('hybrid-text-v1');
  expect(hades.conflicts).toEqual([]);
  expect(hades.unresolved_preferences?.join(' ')).toContain('repetition');
  expect(hades.effective_criteria.price_operator).toBe('lt');
  if (process.env.QUERY_MODEL_PATH) expect(hades.capabilities?.semantic_query_matching).toBe(true);
  expect(hades.capabilities?.ai_interpretation).toBe(false);
  const refined = await discover('story_refinement', { query: 'More story, keep my other limits.', favorite_ids: [1145360], conversation: {
    criteria: hades.effective_criteria, messages: [{ role: 'user', content: acceptance }, { role: 'assistant', content: hades.assistant_message }] } });
  expect(refined.effective_criteria).toEqual(hades.effective_criteria);
  expect(refined.effective_query).toContain('combat');
  expect(refined.effective_query).toContain('More story');
  const conflictRequest: DiscoverRequest = { query: 'under $30', favorite_ids: [1145360], filters: hades.effective_criteria };
  const conflict = await discover('budget_conflict', conflictRequest);
  expect(conflict.conflicts?.length).toBeGreaterThan(0);
  expect(conflict.effective_criteria.max_price_cents).toBe(2000);
  const keep = await discover('keep_controls', { ...conflictRequest, resolution: 'controls' });
  expect(keep.effective_criteria.max_price_cents).toBe(2000);
  const change = await discover('accept_text_change', { ...conflictRequest, resolution: 'text' });
  expect(change.effective_criteria.max_price_cents).toBe(3000);
  await discover('text_only', { query: 'story and exploration on Windows under $20', filters: { platforms: ['windows'], max_price_cents: 2000 } });
  const none = await discover('no_silent_relaxation', { query: 'combat', filters: { ...defaultFilters(), required_genres: ['not-a-catalog-genre'] } });
  expect(none.results).toEqual([]);
  const main = await discover('main_seed_discovery', { favorite_ids: [1145360], filters: defaultFilters(), limit: 10 });
  expect(main.ranking_version).toBe('seed-feedback-v1');

  const scans: { device: string; state: string; axe: string[]; overflow: boolean }[] = [];
  const errors: string[] = [];
  for (const size of [{ name: 'desktop', width: 1440, height: 1000 }, { name: 'mobile', width: 390, height: 844 }]) {
    const context = await browser.newContext({ viewport: { width: size.width, height: size.height }, baseURL: frontend });
    const page = await context.newPage();
    page.on('pageerror', (error) => errors.push(error.message));
    const capture = async (state: string) => {
      await page.evaluate(() => document.fonts.ready);
      await page.locator('img').evaluateAll((images: HTMLImageElement[]) => Promise.all(images.map((image) => {
        image.loading = 'eager';
        return image.complete ? undefined : new Promise<void>((resolve) => { image.addEventListener('load', () => resolve(), { once: true }); image.addEventListener('error', () => resolve(), { once: true }); setTimeout(resolve, 5000); });
      })));
      const axe = (await new AxeBuilder({ page }).analyze()).violations.map((item) => item.id);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
      expect(axe).toEqual([]); expect(overflow).toBe(false);
      scans.push({ device: size.name, state, axe, overflow });
      await page.evaluate(() => scrollTo(0, 0));
      await page.screenshot({ path: path.join(captures, `${state}-${size.name}.png`), fullPage: true });
    };
    await page.goto('/');
    await expect(page.getByRole('slider', { name: 'Maximum recorded price', exact: true })).toBeEnabled({ timeout: 20000 });
    await capture('initial');
    await expect(page.getByRole('textbox', { name: 'What are you looking for?' })).toHaveCount(0);
    const waitForAnswer = () => page.waitForResponse((reply) => reply.url() === `${api}/api/v1/discover`, { timeout: 75000 });
    const answer = waitForAnswer();
    await page.getByRole('button', { name: 'Find my next game', exact: true }).click();
    const result = await answer;
    expect(result.status()).toBe(200); expect(result.headers()['access-control-allow-origin']).toBe(frontend);
    await expect(page.locator('.study-game')).toHaveCount(main.results.length);
    await capture('main-results');
    const ids = await page.locator('.study-game h3').evaluateAll(headings => headings.map(heading => heading.id));
    await page.locator('.study-game').first().getByRole('button', { name: 'Not For Me', exact: true }).click();
    await expect(page.locator('.study-game')).toHaveCount(main.results.length - 1);
    expect(await page.locator('.study-game h3').evaluateAll(headings => headings.map(heading => heading.id))).toEqual(ids.slice(1));
    await capture('dismissed');
    await page.getByRole('button', { name: 'Ask the assistant', exact: true }).click();
    await capture('assistant-open');
    await page.getByRole('textbox', { name: 'Message the assistant' }).fill('Linux co-op under $40');
    const chatAnswer = page.waitForResponse(reply => reply.url() === `${api}/api/v1/chat`);
    await page.getByRole('button', { name: 'Send message', exact: true }).click();
    expect((await chatAnswer).status()).toBe(503);
    await expect(page.getByRole('alert')).toContainText('AI chat is not enabled');
    expect(await page.evaluate(() => JSON.parse(localStorage.getItem('game-discovery:guest')!).preferences.max_price_cents)).toBe(2000);
    await capture('assistant-unavailable');
    await page.getByRole('button', { name: 'Close game assistant', exact: true }).click();
    await page.reload();
    await page.getByRole('button', { name: 'Ask the assistant', exact: true }).click();
    await expect(page.getByRole('log')).toContainText('Linux co-op under $40');
    await capture('session-reload');
    await page.getByRole('button', { name: 'Close game assistant', exact: true }).click();
    await page.getByText('Your device data', { exact: true }).click();
    await page.getByRole('button', { name: 'Clear my saved data', exact: true }).click();
    expect(await page.evaluate(() => sessionStorage.getItem('game-discovery:assistant'))).toBeNull();
    await page.goto('/current-original.html');
    await expect(page.getByRole('button', { name: 'Ask the assistant', exact: true })).toBeVisible();
    await context.close();
  }
  expect(errors).toEqual([]);
  const report = { status: 'passed', observed_at: new Date().toISOString(), catalog_version: hades.catalog_version,
    ranking_version: hades.ranking_version, cases, scans, errors,
    note: 'Owned local API and real restricted catalog; eight API cases include seven legacy text-API compatibility cases. Browser uses independent main discovery and actual disabled-chat endpoint; no live AI. No production migration, import, deployment or evaluated relevance-improvement claim.' };
  await writeFile(path.join(root, 'docs/reports/independent-assistant-browser-live.json'), JSON.stringify(report, null, 2) + '\n');
});
