// Explicit local full-stack M2 check. Starts/stops only its owned children.
/* global document, window */
import { spawn, spawnSync } from 'node:child_process';
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';

const captures = resolve(process.env.M2_CAPTURE_DIR || '../.impeccable/review/m2');
const children = [];
let browser;
function start(command, args, env = process.env) {
  const child = spawn(command, args, { env, stdio: 'ignore', windowsHide: true });
  children.push(child);
  child.on('error', () => { process.exitCode = 1; });
}
async function waitFor(url) {
  for (let attempt = 0; attempt < 375; attempt++) {
    try { if ((await fetch(url)).ok) return; } catch { /* Bounded local startup. */ }
    await new Promise((resolve) => setTimeout(resolve, 200));
  }
  throw new Error('Local service did not start on the documented ports.');
}
try {
  for (const url of ['http://127.0.0.1:8000/health/live', 'http://127.0.0.1:4173']) {
    let occupied = false;
    try { await fetch(url); occupied = true; } catch { /* Require free ports. */ }
    if (occupied) throw new Error('Stop existing servers on 8000/4173 before this check.');
  }
  start(process.env.API_PYTHON || 'python', ['-m', 'uvicorn', 'game_discovery.api.main:app', '--host', '127.0.0.1', '--port', '8000', '--workers', '1'],
    { ...process.env, ALLOWED_ORIGINS: 'http://127.0.0.1:4173' });
  start(process.execPath, ['node_modules/vite/bin/vite.js', 'preview', '--host', '127.0.0.1', '--port', '4173', '--strictPort']);
  await Promise.all([waitFor('http://127.0.0.1:8000/health/live'), waitFor('http://127.0.0.1:4173')]);
  browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto('http://127.0.0.1:4173/');
  await page.getByRole('heading', { name: 'Find your next favorite.' }).waitFor();
  await page.getByLabel('Search the catalog').fill('Hades');
  const searched = page.waitForResponse((response) => response.url().includes('/api/v1/games?q=Hades'));
  await page.getByRole('button', { name: 'Search', exact: true }).click();
  const searchResponse = await searched;
  if (!searchResponse.ok()) throw new Error(`Real catalog search failed (${searchResponse.status()}).`);
  await page.waitForFunction(() => !document.querySelector('.search-status')?.textContent?.includes('Searching'));
  if (!(await page.getByRole('button', { name: 'Hades Add favorite', exact: true }).count())) {
    throw new Error(`Real search did not render the Hades seed: ${await page.locator('.search-status').textContent()}`);
  }
  await page.getByRole('button', { name: 'Hades Add favorite', exact: true }).click();
  await page.getByLabel('Maximum recorded price (USD)').fill('19.99');
  await page.getByLabel('Windows', { exact: true }).check();
  await page.getByText('Play modes, genres & exclusions', { exact: true }).click();
  await page.getByLabel('Single-player', { exact: true }).check();
  const answered = page.waitForResponse((response) => response.url().endsWith('/api/v1/discover'));
  await page.getByRole('button', { name: 'Discover games', exact: true }).click();
  const apiResponse = await answered;
  const body = await apiResponse.json();
  if (!apiResponse.ok() || !body.results.length) throw new Error('Real constrained discovery failed.');
  if (body.results.some(({ game }) => game.app_id === 1145360 || !game.platforms.windows || !game.modes.includes('single-player') || !game.price || game.price.currency !== 'USD' || game.price.amount_cents > 1999)) throw new Error('A hard constraint failed.');
  await page.getByRole('heading', { name: body.results[0].game.title, exact: true }).waitFor();
  await page.getByText('Why this game?', { exact: true }).first().click();
  await page.getByRole('link', { name: /Steam source/ }).first().waitFor();
  await page.evaluate(() => document.fonts.ready);
  await page.locator('img').evaluateAll(async (images) => {
    images.forEach((image) => { image.loading = 'eager'; });
    await Promise.all(images.map((image) => image.complete ? undefined : new Promise((resolve) => {
      image.addEventListener('load', resolve, { once: true }); image.addEventListener('error', resolve, { once: true });
      setTimeout(resolve, 5000);
    })));
  });
  await mkdir(captures, { recursive: true });
  const accessibility = {};
  for (const [name, width, height] of [['desktop', 1440, 900], ['mobile', 390, 844]]) {
    await page.setViewportSize({ width, height });
    await page.evaluate(() => window.scrollTo(0, 0));
    if (await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)) throw new Error(`${name} overflow detected.`);
    accessibility[name] = (await new AxeBuilder({ page }).analyze()).violations.length;
    if (accessibility[name]) throw new Error(`${name} accessibility check failed.`);
    await page.screenshot({ path: resolve(captures, `${name}.png`), fullPage: true, animations: 'disabled' });
  }
  await page.goto(`http://127.0.0.1:4173/games/${body.results[0].game.app_id}`);
  await page.getByRole('heading', { name: body.results[0].game.title, exact: true }).waitFor();
  await page.reload();
  await page.getByRole('heading', { name: body.results[0].game.title, exact: true }).waitFor();
  if (errors.length) throw new Error('Uncaught browser errors detected.');
  const report = { check: 'real-local-m2', catalog_version: body.catalog_version, results: body.results.map(({ game }) => ({ app_id: game.app_id, title: game.title, recorded_cents: game.price.amount_cents })),
    filters: body.effective_criteria, accessibility, browser_errors: errors.length, direct_detail_reload: 'passed', captures };
  await writeFile(resolve(captures, 'report.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify(report));
} finally {
  await browser?.close();
  for (const child of children.reverse()) {
    if (!child.pid) continue;
    if (process.platform === 'win32') spawnSync('taskkill', ['/pid', String(child.pid), '/t', '/f'], { stdio: 'ignore' });
    else child.kill('SIGTERM');
  }
}
