// Exercise real browser CORS + FastAPI + configured PostgreSQL, then stop owned children.
/* global document, window */
import { spawn, spawnSync } from 'node:child_process';
import { mkdir } from 'node:fs/promises';
import { resolve } from 'node:path';
import { chromium } from 'playwright';

const python = process.env.API_PYTHON || 'python';
const captures = resolve(process.env.M1_CAPTURE_DIR || '../.impeccable/review');
const children = [];
let browser;

function start(command, args, env = process.env) {
  const child = spawn(command, args, { env, stdio: 'ignore', windowsHide: true });
  children.push(child);
  child.on('error', () => { process.exitCode = 1; });
  return child;
}

async function waitFor(url) {
  for (let i = 0; i < 50; i++) {
    try { if ((await fetch(url)).ok) return; } catch { /* Local server startup. */ }
    await new Promise((r) => setTimeout(r, 200));
  }
  throw new Error('Local service did not start; check the documented ports and installed backend.');
}

try {
  // Require free ports: never mistake another process's page for this smoke run.
  for (const url of ['http://127.0.0.1:8000/health/live', 'http://127.0.0.1:4173']) {
    let occupied = false;
    try { await fetch(url); occupied = true; } catch { /* Expected, port is free. */ }
    if (occupied) throw new Error('Stop existing local servers on ports 8000/4173 before this check.');
  }
  start(python, ['-m', 'uvicorn', 'game_discovery.api.main:app', '--host', '127.0.0.1', '--port', '8000', '--workers', '1'],
    { ...process.env, ALLOWED_ORIGINS: 'http://127.0.0.1:4173' });
  start(process.execPath, ['node_modules/vite/bin/vite.js', 'preview', '--host', '127.0.0.1', '--port', '4173', '--strictPort']);
  await Promise.all([waitFor('http://127.0.0.1:8000/health/live'), waitFor('http://127.0.0.1:4173')]);
  browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto('http://127.0.0.1:4173/system');
  await page.getByText('API connected', { exact: true }).waitFor();
  const facts = await page.evaluate(async () => {
    const response = await fetch('http://127.0.0.1:8000/api/v1/catalog/status');
    const json = await response.json();
    return { http_status: response.status, state: json.state, game_count: json.game_count };
  });
  if (facts.http_status !== 200 || errors.length) throw new Error('Browser/API contract check failed.');
  await page.evaluate(() => document.fonts.ready);
  await mkdir(captures, { recursive: true });
  await page.screenshot({ path: resolve(captures, 'desktop.png'), fullPage: true, animations: 'disabled' });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: resolve(captures, 'mobile.png'), fullPage: true, animations: 'disabled' });
  if (await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)) throw new Error('Mobile overflow detected.');
  console.log(JSON.stringify({ check: 'real-local-stack', ...facts, browser_errors: errors.length, captures }));
} finally {
  await browser?.close();
  for (const child of children.reverse()) {
    if (!child.pid) continue;
    if (process.platform === 'win32') spawnSync('taskkill', ['/pid', String(child.pid), '/t', '/f'], { stdio: 'ignore' });
    else child.kill('SIGTERM');
  }
}
