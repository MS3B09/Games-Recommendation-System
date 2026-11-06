// Run: node docs/design/dashboard-chart-options.check.mjs [path/to/installed/frontend/package.json]
// Uses the project's existing Playwright and axe packages; no server or live API.
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, '../..');
const require = createRequire(process.argv[2] ? resolve(process.argv[2]) : resolve(root, 'frontend/package.json'));
const { chromium } = require('@playwright/test');
const AxeBuilder = require('@axe-core/playwright').default;
const output = resolve(root, 'data/reports/dashboard-chart-options');
mkdirSync(output, { recursive: true });
const report = { checkedAt: new Date().toISOString(), checks: [], scans: [], errors: [] };
const browser = await chromium.launch({ executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || undefined });
const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
const page = await context.newPage();
const external = [], pageErrors = [];
page.on('request', r => { if (/^https?:/.test(r.url())) external.push(r.url()); });
page.on('pageerror', e => pageErrors.push(e.message));
async function check(name, run) {
  try { await run(); report.checks.push(name); console.log(`PASS ${name}`); }
  catch (error) { report.errors.push({ name, error: String(error) }); console.error(`FAIL ${name}: ${error}`); }
}
try {
  await page.goto(pathToFileURL(resolve(here, 'dashboard-chart-options.html')).href);
  await page.evaluate(() => document.fonts.ready);
  await check('9 visualizations × 4 working versions = 36 previews; no default selections', async () => {
    assert.equal(await page.locator('#gallery > section').count(), 9);
    assert.equal(await page.locator('.preview').count(), 36);
    assert.equal(await page.locator('input:checked').count(), 0);
    assert.deepEqual(await page.locator('#gallery fieldset').evaluateAll(nodes => nodes.map(n => n.querySelectorAll('.option').length)), Array(9).fill(4));
  });
  await check('Every embedded category, count, platform state, year and all 60 words match the checked fixture', async () => {
    const fixture = JSON.parse(readFileSync(resolve(root, 'frontend/tests/analytics-fixture.json'), 'utf8')).data;
    const embedded = await page.evaluate(() => snapshot);
    for (const [key, value] of Object.entries(embedded)) assert.deepEqual(value, fixture[key], key);
    assert.equal(embedded.words.length, 60);
    const aggregate = await page.evaluate(() => rowsFor(charts.find(c => c.id === 'releases')).map(r => r.count));
    assert.deepEqual(aggregate, Array.from({ length: 12 }, (_, i) => fixture.release_years.reduce((n, y) => n + y.months[i], 0)));
  });
  await check('Reference review bars retain all 9 labels/counts; counts scale from zero', async () => {
    const reference = page.locator('#reviews .option').first();
    assert.equal(await reference.locator('.bar-label').first().innerText(), 'Very Positive\n1,091');
    assert.equal(await reference.locator('.fill').first().evaluate(n => n.style.width), '100%');
    assert.equal(await reference.locator('.bars > li').count(), 9);
  });
  await check('Zero categories have no share-strip sliver; count-axis ticks are exact and unique', async () => {
    assert.equal(await page.locator('#free [data-type="strip"] .strip > span').count(), 2);
    const ticks = await page.evaluate(() => {
      const rows = [{ label: 'One', count: 1 }, { label: 'None', count: 0 }];
      const parse = html => new DOMParser().parseFromString(html, 'text/html');
      return { columns: [...parse(columns(rows, 'games')).querySelectorAll('svg > text')].filter(n => n.hasAttribute('x')).map(n => n.textContent), line: [...parse(line(months.map((label, i) => ({ label, count: i === 0 ? 1 : 0 })))).querySelectorAll('svg > text')].map(n => n.textContent) };
    });
    assert.deepEqual(ticks, { columns: ['0', '1'], line: ['0', '1'] });
  });
  await check('Release year updates all four previews AND exact table, retaining chart selection', async () => {
    await page.locator('#releases input').nth(2).check();
    await page.getByLabel('Release year', { exact: true }).selectOption('2006');
    const result = await page.locator('#releases').evaluate(n => ({
      bars: [...n.querySelectorAll('.bars strong')].map(e => e.textContent),
      columns: [...n.querySelectorAll('[data-type="columns"] svg g text')].map(e => e.textContent),
      line: [...n.querySelectorAll('[data-type="line"] svg g text:first-of-type')].map(e => e.textContent),
      heat: [...n.querySelectorAll('.month-cell strong')].map(e => e.textContent),
      table: [...n.querySelectorAll('.exact-values td')].map(e => e.textContent)
    }));
    const expected = ['0','0','0','0','0','0','0','0','0','1','1','0'];
    for (const values of Object.values(result)) assert.deepEqual(values, expected);
    assert.equal(await page.locator('#releases input').nth(2).isChecked(), true);
    await page.getByLabel('Release year', { exact: true }).selectOption('all');
  });
  await check('Native keyboard choices, one per chart, mix into a full export', async () => {
    for (const radios of await page.locator('#gallery fieldset').all()) {
      const first = radios.locator('input').first(); await first.focus(); await page.keyboard.press('Space');
    }
    assert.equal(await page.locator('input:checked').count(), 9);
    assert.equal(await page.locator('#progress').innerText(), '9 of 9 selected');
    await page.locator('#reviews input').nth(1).check();
    assert.equal(await page.locator('input:checked').count(), 9);
    assert.match(await page.locator('#choice-list').inputValue(), /Review type distribution: B — Donut/);
    const wait = page.waitForEvent('download'); await page.getByRole('button', { name: 'Download choices' }).click();
    const download = await wait; assert.equal(download.suggestedFilename(), 'dashboard-chart-choices.txt');
    const path = resolve(output, download.suggestedFilename()); await download.saveAs(path);
    assert.equal(readFileSync(path, 'utf8').trim(), (await page.locator('#choice-list').inputValue()).trim());
  });
  await check('Copy has a usable fallback; hover/tap reads actual values', async () => {
    await page.evaluate(() => Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText: async () => { throw new Error('Simulated clipboard denial'); } } }));
    await page.getByRole('button', { name: 'Copy choices' }).click();
    assert.match(await page.locator('#selection-status').innerText(), /Clipboard access is unavailable/);
    await page.locator('#words .cloud span').first().click();
    assert.equal(await page.locator('#words .reading').first().innerText(), 'world: 422 occurrences');
  });
  await page.getByRole('button', { name: 'Clear selections', exact: true }).click();
  await check('Clear removes only in-page choices; reload is honest and fresh', async () => {
    assert.equal(await page.locator('input:checked').count(), 0);
    await page.reload(); assert.equal(await page.locator('input:checked').count(), 0);
    const source = readFileSync(resolve(here, 'dashboard-chart-options.html'), 'utf8');
    assert.equal(/localStorage|sessionStorage|fetch\(/.test(source), false);
  });
  for (const width of [1440, 390, 320]) {
    await check(`${width}px: all chart layouts accessible, no page overflow, no empty previews`, async () => {
      await page.setViewportSize({ width, height: 1000 });
      const bounds = await page.evaluate(() => ({ overflow: document.documentElement.scrollWidth > innerWidth, empty: [...document.querySelectorAll('.preview')].filter(n => !n.children.length).length }));
      assert.deepEqual(bounds, { overflow: false, empty: 0 });
      const violations = (await new AxeBuilder({ page }).analyze()).violations;
      report.scans.push({ width, overflow: bounds.overflow, violations }); assert.equal(violations.length, 0, JSON.stringify(violations.map(v => ({ id: v.id, nodes: v.nodes.map(n => n.target) }))));
    });
    // One batched render inspection: every desktop section, plus representative narrow layouts.
    const ids = width === 1440 ? ['free','price','discount','releases','genres','platforms','reviews','developers','words'] : ['reviews','platforms','words'];
    for (const id of ids) await page.locator(`#${id}`).screenshot({ path: resolve(output, `${id}-${width}.png`) });
    await page.evaluate(() => scrollTo(0, 0));
    await page.screenshot({ path: resolve(output, `top-${width}.png`) });
  }
  await check('No live API/CDN traffic and no JavaScript page errors', async () => {
    assert.deepEqual(external, []); assert.deepEqual(pageErrors, []);
  });
} finally {
  report.status = report.errors.length ? 'failed' : 'passed';
  writeFileSync(resolve(output, 'verification.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ status: report.status, checks: report.checks.length, errors: report.errors, scans: report.scans.map(s => ({ width: s.width, axe: s.violations.length, overflow: s.overflow })) }, null, 2));
  await browser.close();
}
assert.deepEqual(report.errors, []);
