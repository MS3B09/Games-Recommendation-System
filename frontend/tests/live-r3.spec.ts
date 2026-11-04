import { spawn, spawnSync, type ChildProcess } from 'node:child_process';
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { test, expect } from '@playwright/test';
import type { ChatResponse } from '../src/api/discovery';

const root = path.resolve(import.meta.dirname, '../..');
const api = 'http://127.0.0.1:8002';
let server: ChildProcess | undefined;
test.beforeAll(async () => {
  if (process.env.CI || !process.env.API_PYTHON) throw new Error('Developer-only actual-catalog check: set API_PYTHON to the durable backend interpreter.');
  let occupied = false;
  try { occupied = (await fetch(`${api}/health/live`, { signal: AbortSignal.timeout(2000) })).ok; } catch { /* Start only our owned probe. */ }
  if (occupied) throw new Error('Port 8002 is occupied; stop or choose your existing service separately.');
  server = spawn(process.env.API_PYTHON, ['-m', 'game_discovery.jobs.serve_chat_r3_probe'], { cwd: root,
    env: { ...process.env }, stdio: 'ignore', windowsHide: true });
  let failed = false; server.on('error', () => { failed = true; });
  for (let attempt = 0; attempt < 250; attempt++) {
    if (failed || server.exitCode !== null) throw new Error('Owned R3 probe failed to start. Check the configured catalog/encoder.');
    try { if ((await fetch(`${api}/health/live`, { signal: AbortSignal.timeout(1000) })).ok) return; } catch { /* Bounded startup wait. */ }
    await new Promise(resolve => setTimeout(resolve, 200));
  }
  throw new Error('Owned R3 probe startup timed out.');
});
test.afterAll(() => {
  if (!server?.pid) return;
  if (process.platform === 'win32') spawnSync('taskkill', ['/PID', String(server.pid), '/T', '/F'], { stdio: 'ignore' });
  else server.kill('SIGTERM');
});

test('browser → actual API/catalog/encoder: multiplayer, facts, suitability, reload, exclusions and undo', async ({ page, request }) => {
  const reportPath = path.join(root, 'docs/reports/conversational-rag-r3-live.json');
  const turns: { message: string; ids: number[]; user_turn: number; milliseconds: number }[] = [];
  let lastResponseAt = 0;
  await page.route('https://**/*', route => route.abort()); // No external artwork/font/web requests.
  await page.goto('/');
  await expect(page.getByRole('slider', { name: 'Maximum recorded price', exact: true })).toBeEnabled({ timeout: 30000 });
  const before = await request.post(`${api}/api/v1/discover`, { data: { favorite_ids: [1145360], filters: {
    max_price_cents: 2000, platforms: ['windows'], required_modes: ['single-player'] } } });
  expect(before.status()).toBe(200);
  const mainBefore = await before.json();
  await page.getByRole('button', { name: 'Find my next game', exact: true }).click();
  await expect(page.locator('.study-game')).not.toHaveCount(0, { timeout: 30000 });
  await page.getByRole('button', { name: 'Ask the assistant', exact: true }).click();
  const say = async (message: string): Promise<ChatResponse> => {
    // Honor the real 30-second peer throttle. No fake clock, reset or bypass.
    const remaining = 30100 - (Date.now() - lastResponseAt);
    if (remaining > 0) await new Promise(resolve => setTimeout(resolve, remaining));
    const started = Date.now();
    const reply = page.waitForResponse(response => response.url() === `${api}/api/v1/chat`, { timeout: 75000 });
    await page.getByRole('textbox', { name: 'Message the assistant' }).fill(message);
    await page.getByRole('button', { name: 'Send message', exact: true }).click();
    const response = await reply; lastResponseAt = Date.now();
    expect(response.status()).toBe(200);
    expect(response.headers()['access-control-allow-origin']).toBe('http://127.0.0.1:4173');
    const value = await response.json() as ChatResponse;
    await expect(page.locator('.assistant-thinking')).toHaveCount(0);
    await expect(page.getByRole('alert')).toHaveCount(0);
    expect(value.state.version).toBe(2);
    turns.push({ message, ids: value.games.map(item => item.game.app_id), user_turn: value.state.user_turn, milliseconds: Date.now() - started });
    const stored = await page.evaluate(() => JSON.parse(sessionStorage.getItem('game-discovery:assistant')!));
    expect(stored.state).toEqual(value.state); expect(stored.pending).toBeNull();
    return value;
  };
  const multiplayer = await say('Find multiplayer games');
  expect(multiplayer.games.length).toBeGreaterThan(0);
  expect(multiplayer.games.every(card => card.game.modes?.includes('multiplayer'))).toBe(true);
  const limited = await request.post(`${api}/api/v1/chat`, { data: { message: 'More multiplayer options', state: multiplayer.state } });
  expect(limited.status()).toBe(429); expect(limited.headers()['retry-after']).toBe('30');
  const facts = await say('Does a spiderman game exist?');
  expect(facts.games.map(card => card.game.app_id)).toEqual([1817070]);
  expect(facts.games[0]!.game.modes).toEqual(['single-player']);
  expect(facts.message).toContain('multiplayer');
  expect(facts.state.provenance).toEqual(multiplayer.state.provenance);
  const suitability = await say('Would it meet those requirements?');
  expect(suitability.message).toContain('does not meet');
  await page.reload(); await page.getByRole('button', { name: 'Ask the assistant', exact: true }).click();
  await expect(page.getByRole('log')).toContainText('single-player');
  const more = await say('More multiplayer options');
  expect(more.state.criteria.required_modes).toEqual(['multiplayer']);
  expect(more.state.provenance.required_modes?.user_turn).toBe(1);
  expect(more.games.every(card => card.game.modes?.includes('multiplayer'))).toBe(true);
  const played = await say('I played Spider-Man');
  expect(played.state.exclusions.map(item => item.app_id)).toEqual([1817070]);
  const undo = await say('Include Spider-Man again');
  expect(undo.state.exclusions).toEqual([]);
  expect(undo.state.user_turn).toBe(6);
  const after = await request.post(`${api}/api/v1/discover`, { data: { favorite_ids: [1145360], filters: {
    max_price_cents: 2000, platforms: ['windows'], required_modes: ['single-player'] } } });
  const mainAfter = await after.json();
  expect(mainAfter.results).toEqual(mainBefore.results);
  expect(mainAfter.effective_criteria).toEqual(mainBefore.effective_criteria);
  const diagnostics = await (await request.get(`${api}/__r3_probe`)).json();
  expect(diagnostics.bounded_packets).toBe(true); expect(diagnostics.matched_reservations).toBe(true);
  expect(diagnostics.mock_http_calls).toBe(12); expect(diagnostics.mock_reservations).toBe(12);
  expect(diagnostics.semantic_candidate_queries).toBe(4);
  await mkdir(path.dirname(reportPath), { recursive: true });
  await writeFile(reportPath, JSON.stringify({ status: 'ok', measured_at: new Date().toISOString(), catalog_version: multiplayer.catalog_version,
    turns, real_throttle_429: true, throttle_waited_without_bypass: true, main_result_ids: mainAfter.results.map((item: { game: { app_id: number } }) => item.game.app_id),
    diagnostics, scope: 'Real browser/API/CORS/read-only catalog and pinned encoder; scripted provider HTTP and accounting. Not live interpretation or quality evidence.' }, null, 2) + '\n');
});
